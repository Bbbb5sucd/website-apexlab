/* ========================================
   APEX LABS — PRODUCT PAGE JS
   Language toggle for individual pages
======================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Check if user was in EN mode (from localStorage)
    let currentLang = localStorage.getItem('apex-lang') || 'ar';

    if (currentLang === 'en') {
        applyLang('en');
    }

    function applyLang(lang) {
        if (lang === 'en') {
            document.documentElement.lang = 'en';
            document.documentElement.dir = 'ltr';
            document.body.classList.add('ltr');
        } else {
            document.documentElement.lang = 'ar';
            document.documentElement.dir = 'rtl';
            document.body.classList.remove('ltr');
        }

        document.querySelectorAll('[data-ar][data-en]').forEach(el => {
            el.innerHTML = el.getAttribute('data-' + lang);
        });
    }
});
