# -*- coding: utf-8 -*-
"""Generate favicon.svg, apple-touch-icon.png, assets/og-image.svg|png for Dukan.

The wordmark is shaped with HarfBuzz (feature: swsh) and emitted as real glyph
outlines, so the icons / OG image never depend on the webfont being loaded.

Run:  python tools/make_assets.py
Deps: pip install uharfbuzz fonttools brotli pillow freetype-py
"""
import io
import os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.transform import Transform
from PIL import Image, ImageDraw
import freetype

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTF = os.path.join(ROOT, "thmanyah typeface", "thmanyahsans", "otf",
                   "thmanyahsans-Black.otf")

NIGHT = "#0A0A0A"
RED = "#A92F32"
REDLITE = "#E0474B"
WHITE = "#FFFFFF"
INK3 = "#9A958E"
LINE_DARK = "#262626"

# FreeType on Windows cannot open a path containing non-ASCII folder names
# (this repo lives in ...\دكان\), so every consumer reads the bytes instead.
with open(OTF, "rb") as _f:
    OTF_BYTES = _f.read()

_face = hb.Face(hb.Blob(OTF_BYTES))
UPM = _face.upem
_hbfont = hb.Font(_face)
_hbfont.scale = (UPM, UPM)

_tt = TTFont(io.BytesIO(OTF_BYTES))
_glyphset = _tt.getGlyphSet()
_order = _tt.getGlyphOrder()


def shape(text, features=None, rtl=True):
    """Shape a string. Returns ([(gid, x, y)...], total_advance)."""
    buf = hb.Buffer()
    buf.add_str(text)
    if rtl:
        buf.direction, buf.script, buf.language = "rtl", "Arab", "ar"
    else:
        buf.direction, buf.script, buf.language = "ltr", "Latn", "en"
    hb.shape(_hbfont, buf, features or {})
    run, x, y = [], 0, 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        run.append((info.codepoint, x + pos.x_offset, y + pos.y_offset))
        x += pos.x_advance
        y += pos.y_advance
    return run, x


def _num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def outline(run, scale, ox, oy):
    """Font-unit run -> one SVG path 'd', y-flipped, pen origin at (ox, oy) px."""
    pen = SVGPathPen(_glyphset, ntos=_num)
    for gid, gx, gy in run:
        t = Transform(scale, 0, 0, -scale, ox + gx * scale, oy - gy * scale)
        _glyphset[_order[gid]].draw(TransformPen(pen, t))
    return pen.getCommands()


def ink_bounds(run):
    """Tight ink bounds of a shaped run, in font units (y up)."""
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for gid, gx, gy in run:
        bp = BoundsPen(_glyphset)
        _glyphset[_order[gid]].draw(bp)
        if not bp.bounds:
            continue
        a, b, c, d = bp.bounds
        x0, y0 = min(x0, a + gx), min(y0, b + gy)
        x1, y1 = max(x1, c + gx), max(y1, d + gy)
    return x0, y0, x1, y1


def draw_run(img, run, px, ox, oy, color):
    """Rasterise a shaped run onto a PIL image; (ox, oy) is the pen origin."""
    face = freetype.Face(io.BytesIO(OTF_BYTES))
    face.set_char_size(int(round(px * 64)))
    s = px / UPM
    for gid, gx, gy in run:
        face.load_glyph(gid, freetype.FT_LOAD_RENDER)
        bmp = face.glyph.bitmap
        if bmp.width == 0 or bmp.rows == 0:
            continue
        data = bytes(bytearray(bmp.buffer))
        rows = [data[i * bmp.pitch:i * bmp.pitch + bmp.width]
                for i in range(bmp.rows)]
        mask = Image.frombytes("L", (bmp.width, bmp.rows), b"".join(rows))
        left = int(round(ox + gx * s)) + face.glyph.bitmap_left
        top = int(round(oy - gy * s)) - face.glyph.bitmap_top
        img.paste(Image.new("RGB", mask.size, color), (left, top), mask)


def rounded_mask(size, radius, ss=4):
    m = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1], radius=radius * ss, fill=255)
    return m.resize((size, size), Image.LANCZOS)


LOGO_RUN, LOGO_ADV = shape("دكان", {"swsh": True})
LX0, LY0, LX1, LY1 = ink_bounds(LOGO_RUN)
LW, LH = LX1 - LX0, LY1 - LY0


def logo_fit(box, pad):
    """Scale + pen origin that centres the wordmark's ink in a square box."""
    scale = min((box - 2 * pad) / LW, (box - 2 * pad) / LH)
    ox = (box - LW * scale) / 2 - LX0 * scale
    oy = (box - LH * scale) / 2 + LY1 * scale
    return scale, ox, oy


def favicon_svg(path, box=64, pad=6, radius=14):
    scale, ox, oy = logo_fit(box, pad)
    d = outline(LOGO_RUN, scale, ox, oy)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'role="img" aria-label="دكان">'
        '<rect width="%d" height="%d" rx="%d" fill="%s"/>'
        '<path fill="%s" d="%s"/></svg>' % (box, box, box, box, radius, RED, WHITE, d)
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def icon_png(path, box=180, pad=17, radius=40):
    scale, ox, oy = logo_fit(box, pad)
    img = Image.new("RGB", (box, box), RED)
    draw_run(img, LOGO_RUN, UPM * scale, ox, oy, (255, 255, 255))
    out = Image.new("RGB", (box, box), NIGHT)
    out.paste(img, (0, 0), rounded_mask(box, radius))
    out.save(path, optimize=True)


OG_W, OG_H = 1200, 630
RUN_A, ADV_A = shape("متجرك لازم ")
RUN_B, ADV_B = shape("يبيع.")
RUN_DOM, ADV_DOM = shape("dukan-iq.pages.dev", rtl=False)


def og_layout():
    logo_scale = 78.0 / LH
    head_px = 108.0
    hs = head_px / UPM
    dom_px = 26.0
    content_r = OG_W - 120
    a_ox = content_r - ADV_A * hs
    return dict(
        rail=58, content_r=content_r,
        logo_scale=logo_scale,
        logo_ox=content_r - LX1 * logo_scale, logo_oy=158,
        head_px=head_px, base_y=408,
        a_ox=a_ox, b_ox=a_ox - ADV_B * hs,
        dom_px=dom_px, dom_ox=content_r - ADV_DOM * dom_px / UPM, dom_y=548,
        dash_x=content_r - 116, dash_y=206,
    )


def og_svg(path):
    g = og_layout()
    d_logo = outline(LOGO_RUN, g["logo_scale"], g["logo_ox"], g["logo_oy"])
    hs = g["head_px"] / UPM
    d_a = outline(RUN_A, hs, g["a_ox"], g["base_y"])
    d_b = outline(RUN_B, hs, g["b_ox"], g["base_y"])
    d_dom = outline(RUN_DOM, g["dom_px"] / UPM, g["dom_ox"], g["dom_y"])
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
        'height="%d" role="img" aria-label="دكان — متجرك لازم يبيع.">' % (OG_W, OG_H, OG_W, OG_H),
        '<rect width="%d" height="%d" fill="%s"/>' % (OG_W, OG_H, NIGHT),
        '<rect x="%d" y="0" width="1" height="%d" fill="%s"/>' % (g["rail"], OG_H, LINE_DARK),
        '<rect x="%d" y="0" width="1" height="%d" fill="%s"/>' % (OG_W - g["rail"] - 1, OG_H, LINE_DARK),
        '<rect x="%d" y="%d" width="116" height="5" rx="2.5" fill="%s"/>' % (g["dash_x"], g["dash_y"], RED),
        '<path fill="%s" d="%s"/>' % (WHITE, d_logo),
        '<path fill="%s" d="%s"/>' % (WHITE, d_a),
        '<path fill="%s" d="%s"/>' % (REDLITE, d_b),
        '<path fill="%s" d="%s"/>' % (INK3, d_dom),
        '</svg>',
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def og_png(path):
    g = og_layout()
    img = Image.new("RGB", (OG_W, OG_H), NIGHT)
    dr = ImageDraw.Draw(img)
    dr.rectangle([g["rail"], 0, g["rail"], OG_H], fill=LINE_DARK)
    dr.rectangle([OG_W - g["rail"] - 1, 0, OG_W - g["rail"] - 1, OG_H], fill=LINE_DARK)
    dr.rounded_rectangle([g["dash_x"], g["dash_y"], g["dash_x"] + 116, g["dash_y"] + 5],
                         radius=3, fill=RED)
    draw_run(img, LOGO_RUN, UPM * g["logo_scale"], g["logo_ox"], g["logo_oy"], (255, 255, 255))
    draw_run(img, RUN_A, g["head_px"], g["a_ox"], g["base_y"], (255, 255, 255))
    draw_run(img, RUN_B, g["head_px"], g["b_ox"], g["base_y"], (224, 71, 75))
    draw_run(img, RUN_DOM, g["dom_px"], g["dom_ox"], g["dom_y"], (154, 149, 142))
    img.save(path, optimize=True)


if __name__ == "__main__":
    favicon_svg(os.path.join(ROOT, "favicon.svg"))
    icon_png(os.path.join(ROOT, "apple-touch-icon.png"))
    og_svg(os.path.join(ROOT, "assets", "og-image.svg"))
    og_png(os.path.join(ROOT, "assets", "og-image.png"))
    print("logo glyphs:", [_order[g] for g, _, _ in LOGO_RUN])
    print("ink bounds:", (LX0, LY0, LX1, LY1), "advance:", LOGO_ADV)
    print("wrote favicon.svg, apple-touch-icon.png, assets/og-image.svg, assets/og-image.png")
