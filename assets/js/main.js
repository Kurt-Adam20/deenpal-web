/* DeenPal — Landing Page JS */

/* ── Theme ─────────────────────────────────────────── */
const html = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const THEME_KEY = 'dp_theme';

function setTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
}

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved) { setTheme(saved); return; }
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(prefersDark ? 'dark' : 'light');
}

themeToggle?.addEventListener('click', () => {
  setTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
});

initTheme();

/* ── Nav scroll shadow ──────────────────────────────── */
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav?.classList.toggle('nav--scrolled', window.scrollY > 20);
}, { passive: true });

/* ── Mobile hamburger ───────────────────────────────── */
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger?.addEventListener('click', () => {
  const open = navLinks?.classList.toggle('open');
  hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
  document.body.style.overflow = open ? 'hidden' : '';
});

navLinks?.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    navLinks.classList.remove('open');
    hamburger?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  });
});

/* ── Particles ──────────────────────────────────────── */
function createParticles() {
  const container = document.getElementById('particles');
  if (!container) return;

  const count = window.innerWidth < 768 ? 12 : 22;

  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'particle';

    const isGold = i % 5 === 0;
    const size = isGold ? 2.5 : (i % 3 === 0 ? 2 : 1.5);
    const left = ((i * 71.3 + 5) % 100);
    const startY = 20 + ((i * 6.3) % 70);
    const duration = 5500 + ((i * 830) % 3500);
    const delay = (i * 490) % 2800;

    el.style.cssText = `
      left: ${left}%;
      top: ${startY}%;
      width: ${size}px;
      height: ${size}px;
      background: ${isGold ? 'rgba(201,169,110,0.6)' : 'rgba(255,255,255,0.2)'};
      animation-duration: ${duration}ms;
      animation-delay: ${delay}ms;
    `;

    container.appendChild(el);
  }
}

createParticles();

/* ── Scroll reveal ──────────────────────────────────── */
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('[data-reveal], [data-reveal-right]').forEach(el => {
    observer.observe(el);
  });
}

if ('IntersectionObserver' in window) {
  initReveal();
} else {
  document.querySelectorAll('[data-reveal], [data-reveal-right]').forEach(el => {
    el.classList.add('visible');
  });
}

/* ── Back to top ────────────────────────────────────── */
const backToTop = document.getElementById('backToTop');

window.addEventListener('scroll', () => {
  backToTop?.classList.toggle('visible', window.scrollY > 400);
}, { passive: true });

backToTop?.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

/* ── Pricing toggle ─────────────────────────────────── */
const toggleMonthly = document.getElementById('toggleMonthly');
const toggleYearly = document.getElementById('toggleYearly');
const premiumPrice = document.getElementById('premiumPrice');
const premiumPeriod = document.getElementById('premiumPeriod');

function setPlan(plan) {
  if (!premiumPrice) return;
  if (plan === 'yearly') {
    premiumPrice.textContent = premiumPrice.dataset.yearly || '€2.99';
    if (premiumPeriod) premiumPeriod.textContent = '/ month, billed yearly';
    toggleYearly?.classList.add('active');
    toggleMonthly?.classList.remove('active');
  } else {
    premiumPrice.textContent = premiumPrice.dataset.monthly || '€4.99';
    if (premiumPeriod) premiumPeriod.textContent = '/ month';
    toggleMonthly?.classList.add('active');
    toggleYearly?.classList.remove('active');
  }
}

toggleMonthly?.addEventListener('click', () => setPlan('monthly'));
toggleYearly?.addEventListener('click', () => setPlan('yearly'));

/* ── Year in footer ─────────────────────────────────── */
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

/* ── Screen carousel ────────────────────────────────── */
const screensTrack = document.getElementById('screensTrack');
const screenDots = document.querySelectorAll('.screen-dot');
const screenLabels = document.querySelectorAll('.screen-label');
let currentSlide = 0;
let carouselInterval;

function goToSlide(n) {
  currentSlide = n;
  if (screensTrack) screensTrack.style.transform = `translateX(-${n * 20}%)`;
  screenDots.forEach((d, i) => d.classList.toggle('active', i === n));
  screenLabels.forEach((l, i) => l.classList.toggle('active', i === n));
}

screenDots.forEach((dot, i) => {
  dot.addEventListener('click', () => {
    goToSlide(i);
    resetCarousel();
  });
});

function resetCarousel() {
  clearInterval(carouselInterval);
  carouselInterval = setInterval(() => goToSlide((currentSlide + 1) % 5), 3500);
}

resetCarousel();

/* ── Active nav link on scroll ──────────────────────── */
const sections = document.querySelectorAll('section[id]');
const navLinksAll = document.querySelectorAll('.nav__link');

const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      navLinksAll.forEach(link => {
        link.classList.toggle('nav__link--active', link.getAttribute('href') === `#${id}`);
      });
    }
  });
}, { threshold: 0.4 });

sections.forEach(s => sectionObserver.observe(s));

/* ── Smooth anchor scroll offset for fixed nav ──────── */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const id = this.getAttribute('href').slice(1);
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    e.preventDefault();
    const offset = 72;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});
