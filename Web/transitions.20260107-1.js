(function () {
    'use strict';
    const transitionEl = document.getElementById('pageTransition');
    if (!transitionEl) return;

    const isModifiedClick = (e) => e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0;

    const shouldHandleLink = (a) => {
        if (!a) return false;
        if (a.target && a.target !== '_self') return false;
        if (a.hasAttribute('download')) return false;
        const href = a.getAttribute('href');
        if (!href || href === '#') return false;
        if (href.startsWith('mailto:') || href.startsWith('tel:')) return false;
        if (/^https?:\/\//i.test(href)) {
            try {
                const url = new URL(href, window.location.href);
                if (url.origin !== window.location.origin) return false;
            } catch {
                return false;
            }
        }
        return true;
    };

    const show = () => {
        transitionEl.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    };

    const hide = () => {
        transitionEl.classList.add('hidden');
        document.body.style.overflow = 'auto';
    };

    const scrollToHash = (hash) => {
        const target = document.querySelector(hash);
        if (!target) return;
        const y = (window.scrollY || window.pageYOffset || 0) + target.getBoundingClientRect().top - 80;
        window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
    };

    document.addEventListener('click', (e) => {
        if (isModifiedClick(e)) return;
        const a = e.target instanceof Element ? e.target.closest('a') : null;
        if (!a || !shouldHandleLink(a)) return;

        const href = a.getAttribute('href');
        if (!href) return;

        const url = new URL(href, window.location.href);

        const isSamePath = url.origin === window.location.origin && url.pathname === window.location.pathname;
        const isHashOnly = isSamePath && url.hash;

        show();

        if (isHashOnly) {
            e.preventDefault();
            window.setTimeout(() => {
                try {
                    history.pushState(null, '', url.hash);
                } catch {}
                scrollToHash(url.hash);
                window.setTimeout(() => hide(), 650);
            }, 420);
            return;
        }

        if (url.origin === window.location.origin) {
            e.preventDefault();
            window.setTimeout(() => {
                window.location.href = url.href;
            }, 420);
        }
    });

    window.addEventListener('pageshow', () => {
        hide();
    });
})();

