'use strict';

/* Tucano Time — site behaviour.
   Dependency-free, no network calls, no cookies, no storage. */

(() => {
  const doc = document;
  const header = doc.querySelector('.site-header');
  const navToggle = doc.querySelector('.nav-toggle');
  const nav = doc.getElementById('site-nav');
  const status = doc.getElementById('copy-status');

  /* ---------------------------------------------------------- header shadow */

  if (header) {
    const onScroll = () => header.classList.toggle('is-stuck', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------------------------------------------------------------- mobile nav */

  if (navToggle && nav) {
    const setOpen = (open) => {
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      nav.classList.toggle('is-open', open);
    };

    navToggle.addEventListener('click', () => {
      setOpen(navToggle.getAttribute('aria-expanded') !== 'true');
    });

    nav.addEventListener('click', (event) => {
      if (event.target.closest('a')) setOpen(false);
    });

    doc.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || navToggle.getAttribute('aria-expanded') !== 'true') return;
      setOpen(false);
      navToggle.focus();
    });

    doc.addEventListener('click', (event) => {
      if (navToggle.getAttribute('aria-expanded') !== 'true') return;
      if (header.contains(event.target)) return;
      setOpen(false);
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 860) setOpen(false);
    });
  }

  /* ------------------------------------------------------------- screenshot tabs */

  const tabs = Array.from(doc.querySelectorAll('.tour-tab'));
  const panel = doc.getElementById('tour-panel');
  const image = doc.getElementById('tour-img');
  const url = doc.getElementById('tour-url');
  const kicker = doc.getElementById('tour-kicker');
  const title = doc.getElementById('tour-title');
  const copy = doc.getElementById('tour-copy');

  const selectTab = (tab, focus = false) => {
    if (!tab || !image) return;
    tabs.forEach((item) => {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      item.classList.toggle('is-active', active);
    });
    if (focus) tab.focus();

    const data = tab.dataset;
    image.src = data.img;
    image.alt = data.alt;
    if (url) url.textContent = data.url;
    if (kicker) kicker.textContent = data.kicker;
    if (title) title.textContent = data.title;
    if (copy) copy.textContent = data.copy;
    if (panel) panel.setAttribute('aria-labelledby', tab.id);
  };

  if (tabs.length && panel) {
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => selectTab(tab));
      tab.addEventListener('keydown', (event) => {
        let next = null;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = tabs[(index + 1) % tabs.length];
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === 'Home') next = tabs[0];
        if (event.key === 'End') next = tabs[tabs.length - 1];
        if (!next) return;
        event.preventDefault();
        selectTab(next, true);
      });
    });

    /* Warm the other screenshots once the page is idle. */
    const warm = () => {
      tabs.forEach((tab) => {
        const src = tab.dataset.img;
        if (src) {
          const img = new Image();
          img.src = src;
        }
      });
    };
    if ('requestIdleCallback' in window) requestIdleCallback(warm, { timeout: 2500 });
    else window.setTimeout(warm, 1200);
  }

  /* --------------------------------------------------------------- copy buttons */

  const announce = (message) => {
    if (!status) return;
    status.textContent = message;
    window.clearTimeout(announce.timer);
    announce.timer = window.setTimeout(() => { status.textContent = ''; }, 2200);
  };

  const fallbackCopy = (text) => {
    const area = doc.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.className = 'copy-fallback';
    doc.body.appendChild(area);
    area.select();
    let ok = false;
    try { ok = doc.execCommand('copy'); } catch { ok = false; }
    area.remove();
    return ok;
  };

  doc.querySelectorAll('[data-copy]').forEach((button) => {
    button.addEventListener('click', async () => {
      const source = doc.getElementById(button.dataset.copy);
      if (!source) return;
      const text = source.textContent.replace(/\n+$/, '');
      let ok = false;
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(text);
          ok = true;
        } catch { ok = false; }
      }
      if (!ok) ok = fallbackCopy(text);

      const label = button.textContent;
      button.textContent = ok ? 'Copied' : 'Select & copy';
      button.classList.toggle('is-copied', ok);
      announce(ok ? 'Copied to clipboard' : 'Copy failed — select the text and copy it manually');
      window.setTimeout(() => {
        button.textContent = label;
        button.classList.remove('is-copied');
      }, 2200);
    });
  });

  /* --------------------------------------------------------------------- year */

  const year = doc.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());
})();
