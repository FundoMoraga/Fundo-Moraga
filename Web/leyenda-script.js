(() => {
    'use strict';

    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
    const prefersReducedMotion =
        window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

    const revealAll = () => {
        document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
    };

    const initMobileMenu = () => {
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navLinks = document.querySelector('.nav-links');
        if (!mobileMenuToggle || !navLinks) return;

        mobileMenuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');

            const spans = mobileMenuToggle.querySelectorAll('span');
            if (navLinks.classList.contains('active')) {
                spans[0] && (spans[0].style.transform = 'rotate(45deg) translate(7px, 7px)');
                spans[1] && (spans[1].style.opacity = '0');
                spans[2] && (spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)');
            } else {
                spans[0] && (spans[0].style.transform = '');
                spans[1] && (spans[1].style.opacity = '1');
                spans[2] && (spans[2].style.transform = '');
            }
        });

        document.querySelectorAll('.nav-links a').forEach((link) => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                const spans = mobileMenuToggle.querySelectorAll('span');
                spans.forEach((span) => {
                    span.style.transform = '';
                    span.style.opacity = '1';
                });
            });
        });
    };

    const initShareButtons = () => {
        const buttons = document.querySelectorAll('.share-btn');
        if (!buttons.length) return;

        const pageUrl = () => encodeURIComponent(window.location.href);
        const title = () => encodeURIComponent(document.title);

        buttons.forEach((btn) => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();

                const url = pageUrl();
                const text = title();
                const rawUrl = window.location.href;

                if (navigator.share && btn.classList.contains('whatsapp')) {
                    try {
                        await navigator.share({
                            title: document.title,
                            text: 'La Sombra del Fundo Moraga — La Leyenda',
                            url: rawUrl,
                        });
                        return;
                    } catch {
                        // Fall back to platform URL shares below.
                    }
                }

                let shareUrl = '';
                if (btn.classList.contains('facebook')) {
                    shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                } else if (btn.classList.contains('twitter')) {
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
                } else if (btn.classList.contains('whatsapp')) {
                    shareUrl = `https://wa.me/?text=${text}%20${url}`;
                }

                if (!shareUrl) return;
                window.open(shareUrl, '_blank', 'noopener,noreferrer,width=680,height=520');
            });
        });
    };

    const initReveals = () => {
        const revealEls = Array.from(document.querySelectorAll('.reveal'));
        if (!revealEls.length) return;

        if (prefersReducedMotion || !('IntersectionObserver' in window)) {
            revealAll();
            return;
        }

        const revealInViewNow = () => {
            const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
            revealEls.forEach((el) => {
                if (el.classList.contains('is-visible')) return;
                const rect = el.getBoundingClientRect();
                if (rect.top <= viewportHeight * 0.9 && rect.bottom >= 0) {
                    el.classList.add('is-visible');
                }
            });
        };

        const observer = new IntersectionObserver(
            (entries, obs) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    entry.target.classList.add('is-visible');
                    obs.unobserve(entry.target);
                });
            },
            { threshold: 0.12, rootMargin: '0px 0px -12% 0px' },
        );

        revealEls.forEach((el) => observer.observe(el));
        revealInViewNow();
        window.addEventListener('load', revealInViewNow, { once: true });
    };

    const initChapterNav = ({ getScrollOffset }) => {
        const nav = document.querySelector('.chapter-nav');
        const toggle = nav?.querySelector('.chapter-nav__toggle');
        const list = nav?.querySelector('.chapter-nav__list');
        if (!nav || !toggle || !list) return { updateActiveChapter: () => {} };

        const isMobile = () => window.matchMedia?.('(max-width: 900px)')?.matches ?? false;
        const closeNav = () => {
            nav.classList.remove('is-open');
            toggle.setAttribute('aria-expanded', 'false');
        };

        toggle.addEventListener('click', () => {
            const isOpen = nav.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', String(isOpen));
        });

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Escape') return;
            if (nav.classList.contains('is-open')) closeNav();
        });

        document.addEventListener('click', (e) => {
            if (!isMobile()) return;
            if (!nav.classList.contains('is-open')) return;
            const target = e.target;
            if (!(target instanceof Element)) return;
            if (!nav.contains(target)) closeNav();
        });

        const chapterLinks = Array.from(list.querySelectorAll('a[href^="#"]'));
        const chapters = chapterLinks
            .map((link) => {
                const href = link.getAttribute('href') || '';
                const id = href.startsWith('#') ? href.slice(1) : '';
                const el = id ? document.getElementById(id) : null;
                return el ? { id, el, link } : null;
            })
            .filter(Boolean);

        let lastActiveId = '';

        const setActive = (activeId) => {
            let activeLink = null;
            chapters.forEach(({ id, link }) => {
                const isActive = id === activeId;
                link.classList.toggle('is-active', isActive);
                if (isActive) link.setAttribute('aria-current', 'true');
                else link.removeAttribute('aria-current');
                if (isActive) activeLink = link;
            });

            if (!activeLink || !activeLink.scrollIntoView) return;
            try {
                activeLink.scrollIntoView({
                    behavior: prefersReducedMotion ? 'auto' : 'smooth',
                    block: 'nearest',
                    inline: 'center',
                });
            } catch {}
        };

        const updateActiveChapter = () => {
            if (!chapters.length) return;
            const offset = getScrollOffset();
            const scanLine = offset + window.innerHeight * 0.22;

            let activeId = chapters[0].id;
            for (const chapter of chapters) {
                const top = chapter.el.getBoundingClientRect().top;
                if (top <= scanLine) activeId = chapter.id;
                else break;
            }
            if (activeId === lastActiveId) return;
            lastActiveId = activeId;
            setActive(activeId);
        };

        chapterLinks.forEach((link) => {
            link.addEventListener('click', () => {
                if (isMobile()) closeNav();
            });
        });

        updateActiveChapter();

        return { updateActiveChapter };
    };

    const initScrollAnchors = ({ getScrollOffset, onScrollToTarget }) => {
        const scrollToTarget = (target) => {
            const offset = getScrollOffset();
            const y = target.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({ top: Math.max(0, y), behavior: prefersReducedMotion ? 'auto' : 'smooth' });
        };

        document.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;

            const anchor = target.closest('a[href^="#"]');
            if (!anchor) return;
            const href = anchor.getAttribute('href');
            if (!href || href === '#') return;
            if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

            const el = document.querySelector(href);
            if (!el) return;

            e.preventDefault();
            scrollToTarget(el);
            history.replaceState(null, '', href);
            onScrollToTarget?.();
        });

        window.addEventListener('hashchange', () => {
            const hash = window.location.hash;
            if (!hash) return;
            const el = document.querySelector(hash);
            if (!el) return;
            scrollToTarget(el);
            onScrollToTarget?.();
        });

        if (window.location.hash) {
            const el = document.querySelector(window.location.hash);
            if (el) {
                requestAnimationFrame(() => {
                    scrollToTarget(el);
                    onScrollToTarget?.();
                });
            }
        }
    };

    const initPostFxCanvas = () => {
        const canvas = document.getElementById('postfx-canvas');
        if (!canvas) return () => {};
        if (prefersReducedMotion) return () => {};

        const ctx = canvas.getContext('2d', { alpha: true, desynchronized: true });
        if (!ctx) return () => {};

        let rafId = 0;
        let lastFrameTime = 0;
        let width = 0;
        let height = 0;
        let dpr = 1;

        let noiseCanvas = null;
        let noiseCtx = null;
        let grainPattern = null;

        let scanCanvas = null;
        let scanCtx = null;
        let scanPattern = null;

        const dust = [];
        const createDust = () => {
            dust.length = 0;
            const count = clamp(Math.floor((width * height) / 220000), 18, 64);
            for (let i = 0; i < count; i += 1) {
                dust.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: (Math.random() * 1.8 + 0.4) * dpr,
                    a: Math.random() * 0.35 + 0.08,
                    vx: (Math.random() - 0.5) * 0.12 * dpr,
                    vy: (Math.random() * 0.22 + 0.04) * dpr,
                });
            }
        };

        const rebuildNoise = () => {
            const size = clamp(Math.round(96 * dpr), 72, 180);
            noiseCanvas = noiseCanvas || document.createElement('canvas');
            noiseCanvas.width = size;
            noiseCanvas.height = size;
            noiseCtx = noiseCtx || noiseCanvas.getContext('2d');
            if (!noiseCtx) return;

            const imageData = noiseCtx.createImageData(size, size);
            const { data } = imageData;
            for (let i = 0; i < data.length; i += 4) {
                const v = (Math.random() * 255) | 0;
                data[i] = v;
                data[i + 1] = v;
                data[i + 2] = v;
                data[i + 3] = (Math.random() * 85) | 0;
            }
            noiseCtx.putImageData(imageData, 0, 0);
            grainPattern = ctx.createPattern(noiseCanvas, 'repeat');
        };

        const rebuildScanlines = () => {
            const row = clamp(Math.round(6 * dpr), 4, 14);
            scanCanvas = scanCanvas || document.createElement('canvas');
            scanCanvas.width = 2;
            scanCanvas.height = row;
            scanCtx = scanCtx || scanCanvas.getContext('2d');
            if (!scanCtx) return;

            scanCtx.clearRect(0, 0, scanCanvas.width, scanCanvas.height);
            scanCtx.fillStyle = 'rgba(255,255,255,0.05)';
            scanCtx.fillRect(0, 0, scanCanvas.width, Math.max(1, Math.round(1 * dpr)));
            scanCtx.fillStyle = 'rgba(0,0,0,0.07)';
            scanCtx.fillRect(0, Math.round(row * 0.66), scanCanvas.width, Math.max(1, Math.round(1 * dpr)));

            scanPattern = ctx.createPattern(scanCanvas, 'repeat');
        };

        const resize = () => {
            dpr = clamp(window.devicePixelRatio || 1, 1, 2.25);
            width = Math.max(1, Math.floor(window.innerWidth * dpr));
            height = Math.max(1, Math.floor(window.innerHeight * dpr));
            canvas.width = width;
            canvas.height = height;
            canvas.style.width = '100%';
            canvas.style.height = '100%';

            rebuildNoise();
            rebuildScanlines();
            createDust();
        };

        const draw = (t) => {
            rafId = requestAnimationFrame(draw);
            if (document.hidden) return;

            const frameInterval = 1000 / 14;
            if (t - lastFrameTime < frameInterval) return;
            lastFrameTime = t;

            if (!grainPattern || !scanPattern) {
                rebuildNoise();
                rebuildScanlines();
            }

            ctx.clearRect(0, 0, width, height);
            ctx.save();

            ctx.globalAlpha = 0.32;
            ctx.fillStyle = grainPattern;
            const ox = (Math.random() * 60) | 0;
            const oy = (Math.random() * 60) | 0;
            ctx.translate(ox, oy);
            ctx.fillRect(-ox, -oy, width + ox, height + oy);
            ctx.setTransform(1, 0, 0, 1, 0, 0);

            ctx.globalAlpha = 0.12;
            ctx.fillStyle = scanPattern;
            ctx.fillRect(0, 0, width, height);

            ctx.globalAlpha = 0.22;
            ctx.fillStyle = 'rgba(255,255,255,1)';
            for (const p of dust) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.y > height + 20 * dpr) {
                    p.y = -20 * dpr;
                    p.x = Math.random() * width;
                }
                if (p.x < -20 * dpr) p.x = width + 20 * dpr;
                if (p.x > width + 20 * dpr) p.x = -20 * dpr;

                ctx.globalAlpha = p.a;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.restore();
        };

        resize();
        rafId = requestAnimationFrame(draw);

        const onResize = () => resize();
        window.addEventListener('resize', onResize, { passive: true });
        window.addEventListener('orientationchange', onResize);

        return () => {
            cancelAnimationFrame(rafId);
            window.removeEventListener('resize', onResize);
            window.removeEventListener('orientationchange', onResize);
        };
    };

    const initLeyenda = () => {
        const navbar = document.querySelector('.navbar');
        const chapterNav = document.querySelector('.chapter-nav');
        const root = document.documentElement;

        const syncHeaderVars = () => {
            const navHeight = navbar?.getBoundingClientRect().height ?? 0;
            document.documentElement.style.setProperty('--nav-h', `${Math.round(navHeight)}px`);
        };

        syncHeaderVars();
        window.addEventListener('resize', syncHeaderVars, { passive: true });

        if ('ResizeObserver' in window && navbar) {
            try {
                const ro = new ResizeObserver(() => syncHeaderVars());
                ro.observe(navbar);
            } catch {}
        }

        const getScrollOffset = () => {
            const navHeight = navbar?.getBoundingClientRect().height ?? 0;
            const chapterHeight = chapterNav?.getBoundingClientRect().height ?? 0;
            return Math.round(navHeight + chapterHeight + 20);
        };

        initMobileMenu();
        initShareButtons();
        initReveals();

        const updateHandlers = [];
        const addScrollHandler = (fn) => {
            if (typeof fn === 'function') updateHandlers.push(fn);
        };

        const { updateActiveChapter } = initChapterNav({ getScrollOffset });

        initScrollAnchors({
            getScrollOffset,
            onScrollToTarget: () => updateActiveChapter(),
        });

        const hero = document.getElementById('leyenda-hero');
        const heroVideo = document.getElementById('leyenda-hero-video');

        const initGlobalLantern = () => {
            if (prefersReducedMotion) return () => {};

            let raf = 0;
            let currentX = 50;
            let currentY = 35;
            let targetX = currentX;
            let targetY = currentY;

            const apply = () => {
                raf = requestAnimationFrame(apply);

                const dx = targetX - currentX;
                const dy = targetY - currentY;
                currentX += dx * 0.14;
                currentY += dy * 0.14;

                root.style.setProperty('--mx', `${clamp(currentX, 0, 100).toFixed(2)}%`);
                root.style.setProperty('--my', `${clamp(currentY, 0, 100).toFixed(2)}%`);

                if (Math.abs(dx) < 0.02 && Math.abs(dy) < 0.02) {
                    cancelAnimationFrame(raf);
                    raf = 0;
                }
            };

            const pushTarget = (clientX, clientY) => {
                const w = window.innerWidth || 1;
                const h = window.innerHeight || 1;
                targetX = (clientX / w) * 100;
                targetY = (clientY / h) * 100;
                if (!raf) raf = requestAnimationFrame(apply);
            };

            const onPointerMove = (e) => pushTarget(e.clientX, e.clientY);
            const onPointerDown = (e) => pushTarget(e.clientX, e.clientY);
            const onMouseLeave = () => pushTarget((window.innerWidth || 1) / 2, (window.innerHeight || 1) * 0.35);

            window.addEventListener('pointermove', onPointerMove, { passive: true });
            window.addEventListener('pointerdown', onPointerDown, { passive: true });
            document.addEventListener('mouseleave', onMouseLeave, { passive: true });

            return () => {
                if (raf) cancelAnimationFrame(raf);
                window.removeEventListener('pointermove', onPointerMove);
                window.removeEventListener('pointerdown', onPointerDown);
                document.removeEventListener('mouseleave', onMouseLeave);
            };
        };

        const shouldDisableHeroVideo = () => {
            if (prefersReducedMotion) return true;
            const saveData = navigator.connection?.saveData ?? false;
            return Boolean(saveData);
        };

        if (hero && heroVideo) {
            if (shouldDisableHeroVideo()) {
                try {
                    heroVideo.pause();
                } catch {}
                heroVideo.removeAttribute('autoplay');
                heroVideo.setAttribute('preload', 'none');
            } else {
                const markVideoReady = () => hero.classList.add('has-video');
                const unmarkVideo = () => hero.classList.remove('has-video');

                heroVideo.addEventListener('playing', markVideoReady, { once: true });
                heroVideo.addEventListener('loadeddata', markVideoReady, { once: true });
                heroVideo.addEventListener('loadedmetadata', markVideoReady, { once: true });
                heroVideo.addEventListener('canplay', markVideoReady, { once: true });
                heroVideo.addEventListener('error', unmarkVideo);

                if (heroVideo.readyState >= 1) markVideoReady();

                const tryPlay = () => {
                    heroVideo.play().catch(() => {});
                };

                tryPlay();

                document.addEventListener('visibilitychange', () => {
                    if (document.hidden) {
                        try {
                            heroVideo.pause();
                        } catch {}
                        return;
                    }
                    tryPlay();
                });
            }
        }

        const setHeroParallax = () => {
            if (!hero) return;
            const y = window.scrollY || window.pageYOffset || 0;
            const limit = (hero.offsetHeight || window.innerHeight || 0) * 0.9;
            const shift = clamp(y, 0, limit) * 0.14;
            hero.style.setProperty('--hero-parallax', `${shift.toFixed(1)}px`);
        };

        if (hero && !prefersReducedMotion) {
            let pointerRaf = 0;
            let lastEvent = null;

            const applyPointer = () => {
                pointerRaf = 0;
                if (!lastEvent) return;
                const rect = hero.getBoundingClientRect();
                const x = ((lastEvent.clientX - rect.left) / rect.width) * 100;
                const y = ((lastEvent.clientY - rect.top) / rect.height) * 100;
                hero.style.setProperty('--mx', `${clamp(x, 0, 100).toFixed(2)}%`);
                hero.style.setProperty('--my', `${clamp(y, 0, 100).toFixed(2)}%`);
            };

            hero.addEventListener(
                'pointermove',
                (e) => {
                    lastEvent = e;
                    if (pointerRaf) return;
                    pointerRaf = requestAnimationFrame(applyPointer);
                },
                { passive: true },
            );

            hero.addEventListener('pointerleave', () => {
                hero.style.setProperty('--mx', '50%');
                hero.style.setProperty('--my', '45%');
            });
        }

        const bar = document.querySelector('.reading-progress__bar');
        const setReadingProgress = () => {
            if (!bar) return;
            const scrollTop = window.scrollY || window.pageYOffset || 0;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            const progress = maxScroll > 0 ? clamp(scrollTop / maxScroll, 0, 1) : 0;
            bar.style.width = `${(progress * 100).toFixed(2)}%`;
        };

        const setNavGlow = () => {
            const y = window.scrollY || window.pageYOffset || 0;
            const nav = document.querySelector('.dark-nav');
            if (!nav) return;
            if (y > 100) nav.style.setProperty('box-shadow', '0 10px 40px rgba(212, 175, 55, 0.16)');
            else nav.style.setProperty('box-shadow', 'none');
        };

        addScrollHandler(setHeroParallax);
        addScrollHandler(setReadingProgress);
        addScrollHandler(updateActiveChapter);
        addScrollHandler(setNavGlow);

        let ticking = false;
        const onScroll = () => {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
                ticking = false;
                updateHandlers.forEach((fn) => {
                    try {
                        fn();
                    } catch {}
                });
            });
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onScroll, { passive: true });
        onScroll();

        const cleanupLantern = initGlobalLantern();
        const cleanupPostFx = initPostFxCanvas();

        let konami = [];
        const konamiSequence = [
            'ArrowUp',
            'ArrowUp',
            'ArrowDown',
            'ArrowDown',
            'ArrowLeft',
            'ArrowRight',
            'ArrowLeft',
            'ArrowRight',
            'b',
            'a',
        ];

        document.addEventListener('keydown', (e) => {
            konami.push(e.key);
            konami = konami.slice(-konamiSequence.length);
            if (konami.join(',') !== konamiSequence.join(',')) return;

            document.body.style.animation = 'pulseGold 1.8s ease-in-out 2';
            setTimeout(() => {
                alert('Has desbloqueado la edición de postproducción.');
            }, 260);
        });

        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulseGold {
                0%, 100% { filter: hue-rotate(0deg) saturate(1); }
                50% { filter: hue-rotate(-10deg) saturate(1.35) brightness(1.05); }
            }
        `;
        document.head.appendChild(style);

        window.addEventListener('beforeunload', () => {
            cleanupLantern();
            cleanupPostFx();
        });

        console.log(
            '%cFundo Moraga — Leyenda (Premium Postproduction)',
            'color:#d4af37;font-size:14px;font-weight:700;text-shadow:0 0 10px rgba(212,175,55,.55);',
        );
    };

    try {
        initLeyenda();
    } catch (err) {
        console.error('[Leyenda] Error de inicialización:', err);
        revealAll();
    }
})();
