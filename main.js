/* ============================================================
   دكان — main.js
   كل الأرقام والروابط من هنا. غيّرها بمكان واحد وتنعكس بالصفحة.
   ============================================================ */

const config = {
  phone: '9647817631103',              // رقم الواتساب بصيغة دولية بلا +
  phoneDisplay: '+964 781 763 1103',   // الشكل المعروض بالصفحة
  instagramHandle: '@dukan.platform',
  hours: 48,                           // مدة التسليم بالمعدّل
  prices: { basic: 35, pro: 55 }       // بالألف دينار / شهرياً
};

config.messages = {
  default: 'هلو دكان 👋 أريد أسوي متجر إلكتروني لبراندي',
  basic: `هلو دكان 👋 مهتم بالباقة الأساسية (${config.prices.basic} ألف)`,
  pro: `هلو دكان 👋 مهتم بالباقة الاحترافية (${config.prices.pro} ألف)`
};

/* آراء الزبائن — مطفية لحد ما تجي اقتباسات حقيقية.
   شغّلها: شيل hidden وبدّل data-enabled="false" لـ "true" بالـ HTML،
   وعبّي المصفوفة هنا.
   const testimonials = [
     // replace with real client quotes + permission
     { name: 'اسم الزبون', store: 'اسم المتجر', quote: 'نص الاقتباس الحقيقي.' }
   ];
*/

(function () {
  'use strict';

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ar = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);

  /* ---------- 1. حقن قيم الـ config ---------- */
  const values = {
    hoursAr: ar(config.hours),
    basicAr: ar(config.prices.basic),
    proAr: ar(config.prices.pro),
    phoneDisplay: config.phoneDisplay,
    instagramHandle: config.instagramHandle
  };
  $$('[data-cfg]').forEach(el => {
    const v = values[el.dataset.cfg];
    if (v != null) el.textContent = v;
  });

  $$('[data-wa]').forEach(a => {
    const msg = config.messages[a.dataset.wa] || config.messages.default;
    a.href = `https://wa.me/${config.phone}?text=${encodeURIComponent(msg)}`;
  });

  /* ---------- 2. تتبّع النقرات (يشتغل بلا أداة تحليلات) ---------- */
  function track(cta) {
    const payload = { event: 'cta_click', cta: cta };
    try {
      if (typeof window.gtag === 'function') window.gtag('event', 'cta_click', { cta: cta });
      else if (Array.isArray(window.dataLayer)) window.dataLayer.push(payload);
      else if (typeof window.plausible === 'function') window.plausible('cta_click', { props: { cta: cta } });
      window.dispatchEvent(new CustomEvent('dukan:cta', { detail: payload }));
    } catch (e) { /* no-op */ }
  }
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-cta]');
    if (t) track(t.dataset.cta);
  });

  /* ---------- 3. ظهور تدريجي عند التمرير ---------- */
  $$('[data-stagger]').forEach(group => {
    const seen = new Map();
    $$('[data-reveal]', group).forEach(el => {
      const i = seen.get(el.parentElement) || 0;
      seen.set(el.parentElement, i + 1);
      el.style.setProperty('--d', Math.min(i, 6) * 60 + 'ms');
    });
  });

  const reveals = $$('[data-reveal]');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        en.target.classList.add('is-in');
        obs.unobserve(en.target);
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.04 });
    reveals.forEach(el => io.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('is-in'));
  }

  /* ---------- 4. شريط تقدّم القراءة + زر واتساب العائم ---------- */
  const float = $('#wa-float');
  const finalCta = $('#contact');
  if (float && finalCta && 'IntersectionObserver' in window) {
    new IntersectionObserver(([en]) => {
      float.classList.toggle('is-off', en.isIntersecting);
    }, { threshold: 0.12 }).observe(finalCta);
  }

  /* ---------- 5. عدّاد الـ ٤٨ ساعة ---------- */
  const num = $('[data-count]');
  if (num && 'IntersectionObserver' in window) {
    new IntersectionObserver((entries, obs) => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        obs.unobserve(en.target);
        if (reduce) return;
        const end = config.hours, t0 = performance.now(), dur = 1100;
        const step = t => {
          const p = Math.min((t - t0) / dur, 1);
          num.textContent = ar(Math.round(end * (1 - Math.pow(1 - p, 3))));
          if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }, { threshold: 0.5 }).observe(num);
  }

  /* ---------- 6. الهيدر وشريط التقدّم والقائمة ---------- */
  const header = $('.site-header');
  const bar = $('#progress-bar');
  let ticking = false;
  function onScroll() {
    header.classList.toggle('is-stuck', scrollY > 24);
    if (bar) {
      const max = document.documentElement.scrollHeight - innerHeight;
      bar.style.inlineSize = (max > 0 ? Math.min(scrollY / max, 1) * 100 : 0) + '%';
    }
    ticking = false;
  }
  addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(onScroll);
  }, { passive: true });
  onScroll();

  const burger = $('#burger'), sheet = $('#sheet'), sheetClose = $('#sheet-close');
  let lastFocus = null;

  function openSheet() {
    lastFocus = document.activeElement;
    sheet.hidden = false;
    burger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    const first = $('a, button', sheet);
    if (first) first.focus();
  }
  function closeSheet() {
    sheet.hidden = true;
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    (lastFocus || burger).focus();
  }

  burger.addEventListener('click', openSheet);
  sheetClose.addEventListener('click', closeSheet);
  sheet.addEventListener('click', e => { if (e.target.closest('a')) closeSheet(); });

  document.addEventListener('keydown', e => {
    if (sheet.hidden) return;
    if (e.key === 'Escape') { closeSheet(); return; }
    if (e.key !== 'Tab') return;
    const f = $$('a[href], button', sheet);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ---------- 7. الأسئلة الشائعة: وحدة مفتوحة بس ---------- */
  $$('[data-faq] details').forEach(d => {
    const body = $('.faq-body', d);

    d.addEventListener('toggle', () => {
      if (!d.open) return;
      $$('details[open]', d.parentElement).forEach(o => { if (o !== d) o.open = false; });
    });

    $('summary', d).addEventListener('click', e => {
      if (!d.open || reduce || !body) return;   // الفتح تتكفل بيه الـ CSS
      e.preventDefault();
      d.classList.add('is-closing');
      const done = () => {
        body.removeEventListener('transitionend', done);
        d.classList.remove('is-closing');
        d.open = false;
      };
      body.addEventListener('transitionend', done);
    });
  });

  /* ---------- 8. ميلان التلفون حسب الماوس (ديسكتوب) ---------- */
  const phone = $('#phone');
  if (phone && !reduce && matchMedia('(pointer: fine)').matches) {
    const wrap = phone.closest('.phone-wrap');
    wrap.addEventListener('pointermove', e => {
      const r = wrap.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      phone.style.setProperty('--ry', (x * 12).toFixed(2) + 'deg');
      phone.style.setProperty('--rx', (-y * 12).toFixed(2) + 'deg');
    });
    wrap.addEventListener('pointerleave', () => {
      phone.style.setProperty('--ry', '0deg');
      phone.style.setProperty('--rx', '0deg');
    });
  }
})();
