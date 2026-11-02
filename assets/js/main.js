// Pomorix website: small progressive enhancements. The page works without this file.
(function () {
  'use strict';

  // Header shadow once the page scrolls
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Mobile menu
  var toggle = document.querySelector('.nav-toggle');
  var links = document.getElementById('nav-links');
  if (toggle && links) {
    var setOpen = function (open) {
      links.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      toggle.querySelector('use').setAttribute('href', open ? '#i-close' : '#i-menu');
    };
    toggle.addEventListener('click', function () { setOpen(!links.classList.contains('is-open')); });
    links.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) { setOpen(false); toggle.focus(); }
    });
  }

  // Screenshot carousel buttons
  var gallery = document.getElementById('gallery');
  if (gallery) {
    var buttons = document.querySelectorAll('.gallery-btn');
    var update = function () {
      var max = gallery.scrollWidth - gallery.clientWidth - 2;
      buttons.forEach(function (b) {
        b.disabled = b.dataset.dir === '-1' ? gallery.scrollLeft <= 2 : gallery.scrollLeft >= max;
      });
    };
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        var item = gallery.querySelector('li');
        var step = item ? item.getBoundingClientRect().width + 24 : 260;
        var count = Math.max(1, Math.floor(gallery.clientWidth / step));
        gallery.scrollBy({ left: Number(b.dataset.dir) * step * count, behavior: 'smooth' });
      });
    });
    gallery.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  // Blog: filter articles by topic
  var chips = document.querySelectorAll('.chip[data-filter]');
  var cards = document.querySelectorAll('#post-grid .post-card');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var f = chip.dataset.filter;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c === chip)); });
      cards.forEach(function (card) { card.hidden = f !== 'all' && card.dataset.cat !== f; });
    });
  });

  // Blog: highlight the section being read in the table of contents
  // (the last heading that has reached the top of the screen wins, so jumps and fast scrolls stay correct)
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc a[href^="#"]'));
  if (tocLinks.length) {
    var heads = tocLinks.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var current = -1;
    var spy = function () {
      var line = 130; // just below the sticky header, where contents links land
      var active = -1;
      heads.forEach(function (h, i) { if (h && h.getBoundingClientRect().top <= line) active = i; });
      if (active === current) return;
      if (current >= 0) tocLinks[current].classList.remove('is-active');
      if (active >= 0) tocLinks[active].classList.add('is-active');
      current = active;
    };
    window.addEventListener('scroll', spy, { passive: true });
    spy();
  }

  // Reveal sections as they scroll into view
  var items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-visible'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  items.forEach(function (el) { io.observe(el); });
})();
