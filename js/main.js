/* ========================================
   APEX LABS — JS
   Mobile menu, product filter, scroll
   animations, nav shadow, back to top,
   language toggle (AR / EN).
======================================== */

document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menuBtn');
    const navLinks = document.getElementById('navLinks');
    const nav = document.querySelector('.nav');
    const backToTop = document.getElementById('backToTop');
    const langBtn = document.getElementById('langBtn');
    const loader = document.getElementById('loader');

    let currentLang = 'ar'; // default Arabic

    // ===== Loading Screen =====
    window.addEventListener('load', () => {
        setTimeout(() => {
            loader.classList.add('hidden');
        }, 1200);
    });

    // ===== Mobile menu toggle =====
    menuBtn.addEventListener('click', () => {
        menuBtn.classList.toggle('active');
        navLinks.classList.toggle('open');
    });

    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            menuBtn.classList.remove('active');
            navLinks.classList.remove('open');
        });
    });

    // ===== Nav shadow on scroll =====
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }

        if (window.scrollY > 400) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });

    // ===== Back to top =====
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ===== Language Toggle =====
    langBtn.addEventListener('click', () => {
        if (currentLang === 'ar') {
            currentLang = 'en';
            document.documentElement.lang = 'en';
            document.documentElement.dir = 'ltr';
            document.body.classList.add('ltr');
            langBtn.textContent = 'AR';
        } else {
            currentLang = 'ar';
            document.documentElement.lang = 'ar';
            document.documentElement.dir = 'rtl';
            document.body.classList.remove('ltr');
            langBtn.textContent = 'EN';
        }

        localStorage.setItem('apex-lang', currentLang);

        // Swap all text with data-ar / data-en attributes
        document.querySelectorAll('[data-ar][data-en]').forEach(el => {
            el.innerHTML = el.getAttribute('data-' + currentLang);
        });
    });

    // Restore language preference
    const savedLang = localStorage.getItem('apex-lang');
    if (savedLang === 'en') {
        currentLang = 'en';
        document.documentElement.lang = 'en';
        document.documentElement.dir = 'ltr';
        document.body.classList.add('ltr');
        langBtn.textContent = 'AR';
        document.querySelectorAll('[data-ar][data-en]').forEach(el => {
            el.innerHTML = el.getAttribute('data-en');
        });
    }

    // ===== Product filter tabs =====
    const filterBtns = document.querySelectorAll('.filter-btn');
    const productCards = document.querySelectorAll('.product-card');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.dataset.filter;

            productCards.forEach(card => {
                if (filter === 'all' || card.dataset.category === filter) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        });
    });

    // ===== Scroll Animations =====
    function setupScrollAnimations() {
        document.querySelectorAll('.product-card').forEach((el, i) => {
            el.classList.add('animate-on-scroll', 'slide-up');
            el.style.transitionDelay = `${i * 0.1}s`;
        });

        document.querySelectorAll('.about-card').forEach((el, i) => {
            el.classList.add('animate-on-scroll', 'slide-up');
            el.style.transitionDelay = `${i * 0.15}s`;
        });

        document.querySelectorAll('.section-title').forEach(el => {
            el.classList.add('animate-on-scroll', 'slide-up');
        });
        document.querySelectorAll('.section-desc').forEach(el => {
            el.classList.add('animate-on-scroll', 'slide-up');
            el.style.transitionDelay = '0.1s';
        });

        const heroInner = document.querySelector('.hero-inner');
        if (heroInner) heroInner.classList.add('animate-on-scroll', 'scale-up');

        const filterTabs = document.querySelector('.filter-tabs');
        if (filterTabs) {
            filterTabs.classList.add('animate-on-scroll', 'slide-up');
            filterTabs.style.transitionDelay = '0.15s';
        }

        const contactPlaceholder = document.querySelector('.contact-placeholder');
        if (contactPlaceholder) contactPlaceholder.classList.add('animate-on-scroll', 'scale-up');

        const locationInfo = document.querySelector('.location-info');
        if (locationInfo) {
            locationInfo.classList.add('animate-on-scroll', 'slide-up');
            locationInfo.style.transitionDelay = '0.2s';
        }

        const comingSoon = document.querySelector('.coming-soon');
        if (comingSoon) comingSoon.classList.add('animate-on-scroll', 'slide-up');

        document.querySelectorAll('.testimonial-card').forEach((el, i) => {
            el.classList.add('animate-on-scroll', 'slide-up');
            el.style.transitionDelay = `${i * 0.12}s`;
        });
    }

    setupScrollAnimations();

    const allAnimated = document.querySelectorAll('.animate-on-scroll');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    allAnimated.forEach(el => observer.observe(el));
});
