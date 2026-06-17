/**
 * CUSTOM CURSOR - FUNDO MORAGA
 * Cursor realista de llama/fuego con física, chispas y transiciones
 * Inspirado en maicillomoraga.com pero adaptado para Fundo Moraga
 */

(() => {
    'use strict';

    const supportsFinPointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!supportsFinPointer) return;

    // ============================================
    // CONFIGURACIÓN
    // ============================================
    const config = {
        interactiveSelectors: [
            'a', 'button', 'input', 'textarea', 'select',
            '[role="button"]', '.btn', '.card', 'nav a',
            '[data-interactive]', '.hover-lift', '.hover-glow'
        ].join(', '),
        particleCount: 16,
        particleMaxLife: 0.8,
        particleDecay: 0.022,
        followerInertia: 0.12,
        soundVolume: 0.018,
        ambientSize: 320,
        motionDamping: 0.82,
        maxVelocity: 26
    };

    // ============================================
    // ELEMENTOS DOM
    // ============================================
    let customCursor = null;
    let customCursorFollower = null;
    let customCursorGlow = null;
    let customCursorAmbient = null;
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let followerX = mouseX;
    let followerY = mouseY;
    let lastMouseX = mouseX;
    let lastMouseY = mouseY;
    let velocityX = 0;
    let velocityY = 0;
    let motionEnergy = 0;
    let hoverEnergy = 0;
    let isInteractive = false;

    const root = document.documentElement;

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

    const setEnvironmentLight = (x, y, intensity, stretch, tilt) => {
        const normalizedIntensity = clamp(intensity, 0, 1);
        const clampedStretch = clamp(stretch, 0.92, 1.45);
        const auraSize = config.ambientSize + normalizedIntensity * 180;

        root.style.setProperty('--cursor-x', `${x.toFixed(1)}px`);
        root.style.setProperty('--cursor-y', `${y.toFixed(1)}px`);
        root.style.setProperty('--cursor-intensity', normalizedIntensity.toFixed(3));
        root.style.setProperty('--cursor-stretch', clampedStretch.toFixed(3));
        root.style.setProperty('--cursor-tilt', `${tilt.toFixed(2)}deg`);
        root.style.setProperty('--cursor-aura-size', `${auraSize.toFixed(1)}px`);
    };

    const initCursor = () => {
        // Cursor principal (círculo interior)
        customCursor = document.createElement('div');
        customCursor.id = 'customCursor';
        customCursor.className = 'custom-cursor';
        document.body.appendChild(customCursor);

        // Cursor follower (círculo exterior animado)
        customCursorFollower = document.createElement('div');
        customCursorFollower.id = 'customCursorFollower';
        customCursorFollower.className = 'custom-cursor-follower';
        document.body.appendChild(customCursorFollower);

        // Glow effect
        customCursorGlow = document.createElement('div');
        customCursorGlow.id = 'customCursorGlow';
        customCursorGlow.className = 'custom-cursor-glow';
        document.body.appendChild(customCursorGlow);

        // Luz ambiental para interactuar con el entorno.
        customCursorAmbient = document.createElement('div');
        customCursorAmbient.id = 'customCursorAmbient';
        customCursorAmbient.className = 'custom-cursor-ambient';
        document.body.appendChild(customCursorAmbient);

        // Ocultar cursor por defecto
        document.body.style.cursor = 'none';

        setEnvironmentLight(mouseX, mouseY, 0.32, 1, 0);
    };

    const setCursorPosition = (x, y) => {
        if (customCursor) {
            customCursor.style.left = `${x}px`;
            customCursor.style.top = `${y}px`;
        }
        if (customCursorGlow) {
            customCursorGlow.style.left = `${x}px`;
            customCursorGlow.style.top = `${y}px`;
        }
        if (customCursorAmbient) {
            customCursorAmbient.style.left = `${x}px`;
            customCursorAmbient.style.top = `${y}px`;
        }
    };

    // ============================================
    // PARTÍCULAS / TRAIL
    // ============================================
    let particles = [];
    const spawnParticle = (x, y) => {
        const particle = document.createElement('span');
        particle.className = 'cursor-trail-spark';
        
        // Velocidad angular para efecto de giro
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.5 + Math.random() * 1.5;
        
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        document.body.appendChild(particle);

        particles.push({
            el: particle,
            x, y,
            vx: Math.cos(angle) * speed * (Math.random() > 0.5 ? 1 : -0.5),
            vy: Math.sin(angle) * speed * 0.8 - 0.3, // Sube ligeramente
            life: 1,
            decay: config.particleDecay + Math.random() * 0.01,
            scale: 0.4 + Math.random() * 0.8,
            hue: 15 + Math.random() * 50, // Naranja a rojo
            maxLife: config.particleMaxLife,
            skew: -8 + Math.random() * 16
        });

        if (particles.length > config.particleCount) {
            const old = particles.shift();
            try { old?.el?.remove(); } catch {}
        }
    };

    const animateParticles = () => {
        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];
            p.life -= p.decay;
            p.x += p.vx;
            p.y += p.vy;
            p.vx *= 0.985;
            p.vy *= 0.98;
            p.scale *= 0.992;

            if (p.life <= 0) {
                try { p.el.remove(); } catch {}
                particles.splice(i, 1);
                continue;
            }

            p.el.style.left = `${p.x}px`;
            p.el.style.top = `${p.y}px`;
            const opacity = Math.max(0, Math.min(1, p.life));
            const saturation = 100 - (1 - p.life) * 30; // Desaturar al morir
            p.el.style.opacity = `${opacity * 0.7}`;
            p.el.style.transform = `translate(-50%, -50%) scale(${p.scale}) rotate(${p.skew}deg)`;
            p.el.style.filter = `hue-rotate(${p.hue}deg) saturate(${saturation}%)`;
        }
        requestAnimationFrame(animateParticles);
    };

    // ============================================
    // ANIMACIÓN PRINCIPAL
    // ============================================
    const animateFollower = () => {
        followerX += (mouseX - followerX) * config.followerInertia;
        followerY += (mouseY - followerY) * config.followerInertia;

        velocityX *= config.motionDamping;
        velocityY *= config.motionDamping;
        hoverEnergy += ((isInteractive ? 1 : 0) - hoverEnergy) * 0.14;

        const speed = Math.hypot(velocityX, velocityY);
        const normalizedSpeed = clamp(speed / config.maxVelocity, 0, 1);
        motionEnergy += (normalizedSpeed - motionEnergy) * 0.12;
        const intensity = clamp(0.28 + motionEnergy * 0.55 + hoverEnergy * 0.24, 0.18, 1);
        const stretch = 1 + motionEnergy * 0.3 + hoverEnergy * 0.12;
        const tilt = clamp(velocityX * 2.4, -18, 18);

        setEnvironmentLight(followerX, followerY, intensity, stretch, tilt);

        if (customCursorFollower) {
            customCursorFollower.style.left = `${followerX}px`;
            customCursorFollower.style.top = `${followerY}px`;
            customCursorFollower.style.setProperty('--cursor-tilt', `${tilt.toFixed(2)}deg`);
            customCursorFollower.style.setProperty('--cursor-stretch', stretch.toFixed(3));
            customCursorFollower.style.setProperty('--cursor-intensity', intensity.toFixed(3));
        }

        if (customCursor) {
            customCursor.style.setProperty('--cursor-tilt', `${tilt.toFixed(2)}deg`);
            customCursor.style.setProperty('--cursor-stretch', stretch.toFixed(3));
            customCursor.style.setProperty('--cursor-intensity', intensity.toFixed(3));
        }

        if (customCursorGlow) {
            customCursorGlow.style.setProperty('--cursor-intensity', intensity.toFixed(3));
            customCursorGlow.style.setProperty('--cursor-stretch', stretch.toFixed(3));
        }

        if (customCursorAmbient) {
            customCursorAmbient.style.setProperty('--cursor-intensity', intensity.toFixed(3));
            customCursorAmbient.style.setProperty('--cursor-stretch', stretch.toFixed(3));
        }

        requestAnimationFrame(animateFollower);
    };

    // ============================================
    // EVENT LISTENERS
    // ============================================
    const initEventListeners = () => {
        document.addEventListener('pointermove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;

            velocityX += mouseX - lastMouseX;
            velocityY += mouseY - lastMouseY;
            lastMouseX = mouseX;
            lastMouseY = mouseY;

            setCursorPosition(mouseX, mouseY);

            // Generar partículas ocasionalmente
            if (Math.random() > (0.78 - clamp(Math.hypot(velocityX, velocityY) / 70, 0, 0.22))) {
                spawnParticle(followerX, followerY);
            }
        }, { passive: true });

        // Interactividad (scale al hover)
        document.addEventListener('pointerover', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            
            if (target.closest(config.interactiveSelectors)) {
                isInteractive = true;
                customCursor?.classList.add('scale');
                customCursorFollower?.classList.add('scale');
                customCursorGlow?.classList.add('scale');
                customCursorAmbient?.classList.add('scale');
            }
        }, { passive: true });

        document.addEventListener('pointerout', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            
            if (target.closest(config.interactiveSelectors)) {
                isInteractive = false;
                customCursor?.classList.remove('scale');
                customCursorFollower?.classList.remove('scale');
                customCursorGlow?.classList.remove('scale');
                customCursorAmbient?.classList.remove('scale');
            }
        }, { passive: true });

        document.addEventListener('pointerdown', () => {
            customCursor?.classList.add('is-pressed');
            customCursorFollower?.classList.add('is-pressed');
            customCursorGlow?.classList.add('is-pressed');
            customCursorAmbient?.classList.add('is-pressed');
        }, { passive: true });

        document.addEventListener('pointerup', () => {
            customCursor?.classList.remove('is-pressed');
            customCursorFollower?.classList.remove('is-pressed');
            customCursorGlow?.classList.remove('is-pressed');
            customCursorAmbient?.classList.remove('is-pressed');
        }, { passive: true });

        // Visible/invisible
        document.addEventListener('mouseleave', () => {
            customCursor?.classList.add('is-hidden');
            customCursorFollower?.classList.add('is-hidden');
            customCursorGlow?.classList.add('is-hidden');
            customCursorAmbient?.classList.add('is-hidden');
        });

        document.addEventListener('mouseenter', () => {
            customCursor?.classList.remove('is-hidden');
            customCursorFollower?.classList.remove('is-hidden');
            customCursorGlow?.classList.remove('is-hidden');
            customCursorAmbient?.classList.remove('is-hidden');
        });

        window.addEventListener('blur', () => {
            isInteractive = false;
            customCursor?.classList.remove('scale', 'is-pressed');
            customCursorFollower?.classList.remove('scale', 'is-pressed');
            customCursorGlow?.classList.remove('scale', 'is-pressed');
            customCursorAmbient?.classList.remove('scale', 'is-pressed');
        });
    };

    // ============================================
    // INICIALIZACIÓN
    // ============================================
    if (!prefersReducedMotion) {
        initCursor();
        initEventListeners();
        animateFollower();
        animateParticles();
    }
})();
