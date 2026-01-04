// ============================================
// NAVIGATION
// ============================================
const navbar = document.querySelector('.navbar');
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');

// Preloader
window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    setTimeout(() => {
        preloader.classList.add('hidden');
        // Start animations after preloader
        document.body.style.overflow = 'auto';
    }, 1000);
});

// Sticky navbar on scroll
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 5px 30px rgba(0, 0, 0, 0.15)';
    } else {
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    }
});

// Mobile menu toggle
mobileMenuToggle?.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    
    // Animate hamburger
    const spans = mobileMenuToggle.querySelectorAll('span');
    if (navLinks.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(7px, 7px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
    } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '1';
        spans[2].style.transform = '';
    }
});

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('active');
        const spans = mobileMenuToggle?.querySelectorAll('span');
        spans?.forEach(span => {
            span.style.transform = '';
            span.style.opacity = '1';
        });
    });
});

// ============================================
// SMOOTH SCROLL
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href !== '') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        }
    });
});

// ============================================
// SCROLL ANIMATIONS
// ============================================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all service cards, gallery items, etc.
document.querySelectorAll('.service-card, .gallery-item, .info-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});

// ============================================
// HERNANDO CHAT WIDGET
// ============================================
const chatToggle = document.getElementById('chatToggle');
const chatWindow = document.getElementById('chatWindow');
const chatClose = document.getElementById('chatClose');
const chatSend = document.getElementById('chatSend');
const chatInput = document.getElementById('chatInput');
const chatBody = document.getElementById('chatBody');
const chatBadge = document.querySelector('.chat-badge');

// Configuration
const RAILWAY_API_URL = '/hernando'; // Proxy interno vía nginx a Railway

// Toggle chat window
chatToggle?.addEventListener('click', () => {
    chatWindow.classList.toggle('active');
    if (chatWindow.classList.contains('active')) {
        chatInput.focus();
        // Hide badge when opened
        if (chatBadge) chatBadge.style.display = 'none';
    }
});

chatClose?.addEventListener('click', () => {
    chatWindow.classList.remove('active');
});

// Send message function
async function sendMessage(message) {
    if (!message.trim()) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        // Call Hernando API
        const response = await fetch(`${RAILWAY_API_URL}/webhook`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                platform: 'web',
                userId: getOrCreateUserId(),
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            typingIndicator.remove();
            addMessageToChat(data.message || data.response || 'Gracias por tu mensaje. Te responderé pronto.', 'bot');
        } else {
            throw new Error('Error en la respuesta');
        }
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessageToChat('Lo siento, hay un problema de conexión. Por favor intenta más tarde o contáctanos al +56 9 4124 2609', 'bot');
    }
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Add message to chat UI
function addMessageToChat(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const messageP = document.createElement('p');
    messageP.textContent = text;
    
    messageDiv.appendChild(messageP);
    chatBody.appendChild(messageDiv);
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Add typing indicator
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot typing-indicator';
    typingDiv.innerHTML = '<p>Hernando está escribiendo...</p>';
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return typingDiv;
}

// Get or create user ID
function getOrCreateUserId() {
    let userId = localStorage.getItem('hernando_user_id');
    if (!userId) {
        userId = 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('hernando_user_id', userId);
    }
    return userId;
}

// Send message on button click
chatSend?.addEventListener('click', () => {
    sendMessage(chatInput.value);
});

// Send message on Enter key
chatInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(chatInput.value);
    }
});

// Handle all "Reservar con Hernando" buttons
document.querySelectorAll('.btn-reserva, .btn-hernando').forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        chatWindow.classList.add('active');
        chatInput.focus();
        if (chatBadge) chatBadge.style.display = 'none';
    });
});

// ============================================
// GALLERY LIGHTBOX (Optional Enhancement)
// ============================================
document.querySelectorAll('.gallery-item').forEach(item => {
    item.addEventListener('click', () => {
        const img = item.querySelector('img');
        if (img) {
            // You can add a lightbox library here or create custom lightbox
            window.open(img.src, '_blank');
        }
    });
});

// ============================================
// PERFORMANCE: Lazy Loading Images
// ============================================
if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.src = img.dataset.src || img.src;
    });
} else {
    // Fallback for browsers that don't support lazy loading
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// ============================================
// ANALYTICS (Optional)
// ============================================
function trackEvent(category, action, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
    console.log('Event:', category, action, label);
}

// Track important interactions
document.querySelectorAll('.btn-primary, .btn-reserva').forEach(button => {
    button.addEventListener('click', () => {
        trackEvent('Engagement', 'Button Click', button.textContent);
    });
});

// ============================================
// CONSOLE MESSAGE
// ============================================
console.log('%c¡Bienvenido a Fundo Moraga! 🌿', 'font-size: 20px; color: #2c5530; font-weight: bold;');
console.log('%cSitio desarrollado con 💚', 'font-size: 14px; color: #666;');

// ============================================
// PARTICLES.JS INITIALIZATION
// ============================================
if (document.getElementById('particles-js')) {
    particlesJS('particles-js', {
        particles: {
            number: {
                value: 80,
                density: {
                    enable: true,
                    value_area: 800
                }
            },
            color: {
                value: '#d4af37'
            },
            shape: {
                type: 'circle',
                stroke: {
                    width: 0,
                    color: '#000000'
                }
            },
            opacity: {
                value: 0.3,
                random: true,
                anim: {
                    enable: true,
                    speed: 1,
                    opacity_min: 0.1,
                    sync: false
                }
            },
            size: {
                value: 3,
                random: true,
                anim: {
                    enable: true,
                    speed: 2,
                    size_min: 0.1,
                    sync: false
                }
            },
            line_linked: {
                enable: true,
                distance: 150,
                color: '#d4af37',
                opacity: 0.2,
                width: 1
            },
            move: {
                enable: true,
                speed: 2,
                direction: 'none',
                random: false,
                straight: false,
                out_mode: 'out',
                bounce: false
            }
        },
        interactivity: {
            detect_on: 'canvas',
            events: {
                onhover: {
                    enable: true,
                    mode: 'grab'
                },
                onclick: {
                    enable: true,
                    mode: 'push'
                },
                resize: true
            },
            modes: {
                grab: {
                    distance: 140,
                    line_linked: {
                        opacity: 0.5
                    }
                },
                push: {
                    particles_nb: 4
                }
            }
        },
        retina_detect: true
    });
}

// ============================================
// STATS COUNTER ANIMATION
// ============================================
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target + '+';
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current) + '+';
        }
    }, 16);
}

// Observe stats section
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const target = parseInt(stat.getAttribute('data-target'));
                animateCounter(stat, target);
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const statsSection = document.querySelector('.stats-section');
if (statsSection) {
    statsObserver.observe(statsSection);
}

// ============================================
// TESTIMONIALS CAROUSEL
// ============================================
const testimonialCards = document.querySelectorAll('.testimonial-card');
const dots = document.querySelectorAll('.dot');
let currentTestimonial = 0;
let testimonialInterval;

function showTestimonial(index) {
    testimonialCards.forEach(card => card.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));
    
    testimonialCards[index].classList.add('active');
    dots[index].classList.add('active');
}

function nextTestimonial() {
    currentTestimonial = (currentTestimonial + 1) % testimonialCards.length;
    showTestimonial(currentTestimonial);
}

function startTestimonialCarousel() {
    testimonialInterval = setInterval(nextTestimonial, 5000);
}

function stopTestimonialCarousel() {
    clearInterval(testimonialInterval);
}

// Dot click handlers
dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
        currentTestimonial = index;
        showTestimonial(currentTestimonial);
        stopTestimonialCarousel();
        startTestimonialCarousel();
    });
});

// Start carousel
if (testimonialCards.length > 0) {
    startTestimonialCarousel();
}

// Pause on hover
const testimonialCarousel = document.querySelector('.testimonials-carousel');
if (testimonialCarousel) {
    testimonialCarousel.addEventListener('mouseenter', stopTestimonialCarousel);
    testimonialCarousel.addEventListener('mouseleave', startTestimonialCarousel);
}

// ============================================
// LIGHTBOX GALLERY
// ============================================
// VIDEO PLAYER PREMIUM
// ============================================
const mainVideo = document.getElementById('mainVideo');
const videoOverlay = document.getElementById('videoOverlay');
const playButton = document.getElementById('playButton');
const videoControls = document.getElementById('videoControls');
const playPauseBtn = document.getElementById('playPauseBtn');
const muteBtn = document.getElementById('muteBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');
const progressBar = document.getElementById('progressBar');
const progressFilled = document.getElementById('progressFilled');
const currentTimeDisplay = document.getElementById('currentTime');
const durationDisplay = document.getElementById('duration');
const videoTitleEl = document.querySelector('.video-title h3');
const videoSubtitleEl = document.querySelector('.video-title p');
const videoGalleryGrid = document.getElementById('videoGalleryGrid');

const videoClips = [
    {
        src: 'assets/videos/IMG_2274.mov',
        title: 'Ruta bosque norte',
        description: 'Senderos cerrados, curvas y tracción total entre pinos.',
        tag: 'Ruta forestal',
        duration: '0:42',
        orientation: 'portrait'
    },
    {
        src: 'assets/videos/IMG_2275.mov',
        title: 'Cruce de arroyos',
        description: 'Agua, barro y torque controlado en bajadas técnicas.',
        tag: 'Agua y barro',
        duration: '0:37',
        orientation: 'portrait'
    },
    {
        src: 'assets/videos/IMG_2803.mov',
        title: 'Cumbre al atardecer',
        description: 'Vista 360° de Batuco con luz dorada y polvo en suspensión.',
        tag: 'Golden hour',
        duration: '0:51',
        orientation: 'portrait'
    },
    {
        src: 'assets/videos/IMG_3103.mov',
        title: 'Rocas y escalones',
        description: 'Trayectoria técnica con spotter y control fino del gas.',
        tag: 'Técnico',
        duration: '0:44',
        orientation: 'portrait'
    },
    {
        src: 'assets/videos/IMG_3140.mov',
        title: 'Llanos rápidos',
        description: 'Aceleración en rectas de tierra con ripio suelto.',
        tag: 'Speed run',
        duration: '0:33',
        orientation: 'portrait'
    },
    {
        src: 'assets/videos/IMG_3326.mov',
        title: 'Noche en el fundo',
        description: 'Cielo estrellado y luces de vehículos en caravana.',
        tag: 'Nocturno',
        duration: '0:39',
        orientation: 'portrait'
    }
];

if (mainVideo) {
    // Play button click
    playButton?.addEventListener('click', () => {
        mainVideo.play();
        videoOverlay.classList.add('hidden');
    });

    // Video overlay click
    videoOverlay?.addEventListener('click', () => {
        mainVideo.play();
        videoOverlay.classList.add('hidden');
    });

    // Play/Pause toggle
    playPauseBtn?.addEventListener('click', togglePlayPause);
    mainVideo?.addEventListener('click', togglePlayPause);

    function togglePlayPause() {
        if (mainVideo.paused) {
            mainVideo.play();
        } else {
            mainVideo.pause();
        }
    }

    // Update play/pause icon
    mainVideo?.addEventListener('play', () => {
        playPauseBtn.querySelector('.play-icon').style.display = 'none';
        playPauseBtn.querySelector('.pause-icon').style.display = 'block';
    });

    mainVideo?.addEventListener('pause', () => {
        playPauseBtn.querySelector('.play-icon').style.display = 'block';
        playPauseBtn.querySelector('.pause-icon').style.display = 'none';
    });

    // Mute/Unmute
    muteBtn?.addEventListener('click', () => {
        mainVideo.muted = !mainVideo.muted;
        updateMuteIcon();
    });

    function updateMuteIcon() {
        if (mainVideo.muted) {
            muteBtn.querySelector('.volume-icon').style.display = 'none';
            muteBtn.querySelector('.mute-icon').style.display = 'block';
        } else {
            muteBtn.querySelector('.volume-icon').style.display = 'block';
            muteBtn.querySelector('.mute-icon').style.display = 'none';
        }
    }

    // Fullscreen
    fullscreenBtn?.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            if (mainVideo.parentElement.requestFullscreen) {
                mainVideo.parentElement.requestFullscreen();
            } else if (mainVideo.parentElement.webkitRequestFullscreen) {
                mainVideo.parentElement.webkitRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
        }
    });

    // Progress bar
    mainVideo?.addEventListener('timeupdate', updateProgress);
    progressBar?.addEventListener('click', seek);

    function updateProgress() {
        const percent = (mainVideo.currentTime / mainVideo.duration) * 100;
        progressFilled.style.width = percent + '%';
        
        // Update time displays
        currentTimeDisplay.textContent = formatTime(mainVideo.currentTime);
        durationDisplay.textContent = formatTime(mainVideo.duration);
    }

    function seek(e) {
        const rect = progressBar.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        mainVideo.currentTime = percent * mainVideo.duration;
    }

    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // Show controls on video end
    mainVideo?.addEventListener('ended', () => {
        videoOverlay.classList.remove('hidden');
        playPauseBtn.querySelector('.play-icon').style.display = 'block';
        playPauseBtn.querySelector('.pause-icon').style.display = 'none';
    });

    // Show controls on mousemove
    let controlsTimeout;
    const videoPlayer = document.querySelector('.video-player');
    
    videoPlayer?.addEventListener('mousemove', () => {
        videoControls.classList.add('show');
        clearTimeout(controlsTimeout);
        
        if (!mainVideo.paused) {
            controlsTimeout = setTimeout(() => {
                videoControls.classList.remove('show');
            }, 3000);
        }
    });

    videoPlayer?.addEventListener('mouseleave', () => {
        if (!mainVideo.paused) {
            videoControls.classList.remove('show');
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (mainVideo && isVideoInViewport(mainVideo)) {
            switch(e.key) {
                case ' ':
                case 'k':
                    e.preventDefault();
                    togglePlayPause();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    mainVideo.currentTime = Math.max(0, mainVideo.currentTime - 5);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    mainVideo.currentTime = Math.min(mainVideo.duration, mainVideo.currentTime + 5);
                    break;
                case 'm':
                    e.preventDefault();
                    mainVideo.muted = !mainVideo.muted;
                    updateMuteIcon();
                    break;
                case 'f':
                    e.preventDefault();
                    fullscreenBtn.click();
                    break;
            }
        }
    });

    function isVideoInViewport(element) {
        const rect = element.getBoundingClientRect();
        return rect.top < window.innerHeight && rect.bottom > 0;
    }

    // Set initial duration when metadata loads
    mainVideo?.addEventListener('loadedmetadata', () => {
        durationDisplay.textContent = formatTime(mainVideo.duration);
    });

    // ============================================
    // VIDEO GALLERY → CAMBIA EL VIDEO PRINCIPAL
    // ============================================
    function renderVideoGallery() {
        if (!videoGalleryGrid) return;
        videoGalleryGrid.innerHTML = '';

        videoClips.forEach((clip, index) => {
            const card = document.createElement('div');
            card.className = 'video-card';
            card.dataset.index = index;
            card.innerHTML = `
                <video class="video-thumb" src="${clip.src}" muted playsinline loop preload="metadata"></video>
                <span class="video-chip">${clip.tag}</span>
                <span class="video-duration">${clip.duration}</span>
                <div class="video-play-mini">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M8 5v14l11-7z"/></svg>
                </div>
                <div class="video-meta">
                    <h4>${clip.title}</h4>
                    <p>${clip.description}</p>
                </div>
            `;

            const thumb = card.querySelector('video');
            thumb?.addEventListener('mouseenter', () => thumb.play());
            card.addEventListener('mouseleave', () => thumb?.pause());

            card.addEventListener('click', () => setMainVideo(clip));
            videoGalleryGrid.appendChild(card);
        });
    }

    function setMainVideo(clip) {
        if (!clip || !mainVideo) return;
        const videoPlayer = document.querySelector('.video-player');

        // Ajustar modo retrato o paisaje
        if (clip.orientation === 'portrait') {
            videoPlayer?.classList.add('portrait');
            mainVideo.classList.add('portrait');
        } else {
            videoPlayer?.classList.remove('portrait');
            mainVideo.classList.remove('portrait');
        }

        mainVideo.pause();
        mainVideo.src = clip.src;
        mainVideo.load();

        // Mostrar overlay mientras se prepara el video
        videoOverlay?.classList.remove('hidden');
        playPauseBtn?.querySelector('.play-icon')?.style.setProperty('display', 'block');
        playPauseBtn?.querySelector('.pause-icon')?.style.setProperty('display', 'none');

        if (videoTitleEl) videoTitleEl.textContent = clip.title;
        if (videoSubtitleEl) videoSubtitleEl.textContent = clip.description;

        const attemptPlay = () => {
            mainVideo.play().then(() => {
                videoOverlay?.classList.add('hidden');
                playPauseBtn?.querySelector('.play-icon')?.style.setProperty('display', 'none');
                playPauseBtn?.querySelector('.pause-icon')?.style.setProperty('display', 'block');
            }).catch(() => {
                // Si el navegador bloquea, dejamos overlay visible para interacción manual
                videoOverlay?.classList.remove('hidden');
                playPauseBtn?.querySelector('.play-icon')?.style.setProperty('display', 'block');
                playPauseBtn?.querySelector('.pause-icon')?.style.setProperty('display', 'none');
            });
        };

        // Esperar a que el medio esté listo antes de reproducir
        const onCanPlay = () => {
            mainVideo.removeEventListener('canplay', onCanPlay);
            attemptPlay();
        };

        mainVideo.addEventListener('canplay', onCanPlay, { once: true });
    }

    renderVideoGallery();
}

// Old lightbox code (can be removed if not needed)
const galleryItems = document.querySelectorAll('.gallery-item');
if (galleryItems.length > 0) {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.querySelector('.lightbox-image');
    const lightboxClose = document.querySelector('.lightbox-close');
    const lightboxPrev = document.querySelector('.lightbox-prev');
    const lightboxNext = document.querySelector('.lightbox-next');
    let currentGalleryIndex = 0;
    const galleryImages = Array.from(galleryItems).map(item => ({
        src: item.querySelector('img').src,
        alt: item.querySelector('img').alt
    }));

    function openLightbox(index) {
        currentGalleryIndex = index;
        lightboxImg.src = galleryImages[index].src;
        lightboxImg.alt = galleryImages[index].alt;
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        lightbox.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    function showPrevImage() {
        currentGalleryIndex = (currentGalleryIndex - 1 + galleryImages.length) % galleryImages.length;
        lightboxImg.src = galleryImages[currentGalleryIndex].src;
        lightboxImg.alt = galleryImages[currentGalleryIndex].alt;
    }

    function showNextImage() {
        currentGalleryIndex = (currentGalleryIndex + 1) % galleryImages.length;
        lightboxImg.src = galleryImages[currentGalleryIndex].src;
        lightboxImg.alt = galleryImages[currentGalleryIndex].alt;
    }

    // Gallery item clicks
    galleryItems.forEach((item, index) => {
        item.addEventListener('click', () => openLightbox(index));
    });

    // Lightbox controls
    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightboxPrev) lightboxPrev.addEventListener('click', showPrevImage);
    if (lightboxNext) lightboxNext.addEventListener('click', showNextImage);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!lightbox.classList.contains('active')) return;
        
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') showPrevImage();
        if (e.key === 'ArrowRight') showNextImage();
    });

    // Click outside to close
    lightbox?.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });
}

// ============================================
// CONTACT FORM HANDLING
// ============================================
const contactForm = document.getElementById('contactForm');
const formStatus = document.querySelector('.form-status');

contactForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(contactForm);
    const data = Object.fromEntries(formData);
    
    // Show loading state
    const submitButton = contactForm.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Enviando...';
    submitButton.disabled = true;
    
    try {
        // Here you would integrate with your backend or email service
        // Example: EmailJS, Formspree, or your own API
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // For now, we'll send to Hernando's chat API
        const response = await fetch('https://fm-ia-production.up.railway.app/webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: `Nuevo mensaje de contacto:\nNombre: ${data.name}\nEmail: ${data.email}\nTeléfono: ${data.phone}\nServicio: ${data.service}\nMensaje: ${data.message}`,
                platform: 'web-form',
                userId: getOrCreateUserId(),
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            formStatus.textContent = '¡Mensaje enviado exitosamente! Nos contactaremos contigo pronto.';
            formStatus.className = 'form-status success';
            contactForm.reset();
        } else {
            throw new Error('Error en el envío');
        }
    } catch (error) {
        console.error('Error:', error);
        formStatus.textContent = 'Hubo un error al enviar el mensaje. Por favor intenta de nuevo o contáctanos directamente.';
        formStatus.className = 'form-status error';
    } finally {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        
        // Hide status after 5 seconds
        setTimeout(() => {
            formStatus.style.display = 'none';
        }, 5000);
    }
});

// ============================================
// PARALLAX SCROLL EFFECTS
// ============================================
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    
    // Parallax on hero
    const hero = document.querySelector('.hero');
    if (hero) {
        hero.style.backgroundPositionY = scrolled * 0.5 + 'px';
    }
    
    // Parallax on about image
    const aboutImage = document.querySelector('.about-image');
    if (aboutImage && isInViewport(aboutImage)) {
        aboutImage.style.transform = `translateY(${scrolled * 0.1}px) rotate(2deg)`;
    }
});

function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// ============================================
// SMOOTH REVEAL ANIMATIONS
// ============================================
const revealElements = document.querySelectorAll('.service-card, .gallery-item, .info-card, .testimonial-card, .stat-card');

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            setTimeout(() => {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }, index * 100);
            revealObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
});

revealElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(50px)';
    el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    revealObserver.observe(el);
});

// ============================================
// TILT EFFECT ON SERVICE CARDS
// ============================================
const serviceCards = document.querySelectorAll('.service-card');

serviceCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        card.style.transform = `translateY(-15px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        
        // Update mouse position for glow effect
        card.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
        card.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0) rotateX(0) rotateY(0)';
    });
});

// ============================================
// SCROLL TO TOP BUTTON
// ============================================
const scrollToTop = document.createElement('button');
scrollToTop.className = 'scroll-to-top';
scrollToTop.innerHTML = '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/></svg>';
scrollToTop.setAttribute('aria-label', 'Volver arriba');
document.body.appendChild(scrollToTop);

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 500) {
        scrollToTop.classList.add('visible');
    } else {
        scrollToTop.classList.remove('visible');
    }
});

scrollToTop.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// ============================================
// CUSTOM CURSOR (DESKTOP ONLY)
// ============================================
if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    const cursorFollower = document.createElement('div');
    cursorFollower.className = 'custom-cursor-follower';
    
    document.body.appendChild(cursor);
    document.body.appendChild(cursorFollower);
    
    let mouseX = 0, mouseY = 0;
    let followerX = 0, followerY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        cursor.style.left = mouseX + 'px';
        cursor.style.top = mouseY + 'px';
    });
    
    // Smooth follower
    function animateFollower() {
        followerX += (mouseX - followerX) * 0.1;
        followerY += (mouseY - followerY) * 0.1;
        
        cursorFollower.style.left = followerX + 'px';
        cursorFollower.style.top = followerY + 'px';
        
        requestAnimationFrame(animateFollower);
    }
    animateFollower();
    
    // Scale on interactive elements
    const interactiveElements = document.querySelectorAll('a, button, .gallery-item, .service-card');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.style.transform = 'scale(1.5)';
            cursorFollower.style.transform = 'scale(1.5)';
        });
        el.addEventListener('mouseleave', () => {
            cursor.style.transform = 'scale(1)';
            cursorFollower.style.transform = 'scale(1)';
        });
    });
}

// ============================================
// PRELOADER ENHANCEMENT
// ============================================
window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    
    // Add fade out class
    setTimeout(() => {
        preloader.style.opacity = '0';
        preloader.style.visibility = 'hidden';
        document.body.style.overflow = 'auto';
    }, 800);
    
    // Remove from DOM after transition
    setTimeout(() => {
        preloader.remove();
    }, 1300);
});

// ============================================
// LOADING BAR ON PAGE NAVIGATION
// ============================================
const loadingBar = document.createElement('div');
loadingBar.className = 'page-loading-bar';
document.body.appendChild(loadingBar);

let loadingProgress = 0;
let loadingInterval;

function startLoading() {
    loadingProgress = 0;
    loadingBar.style.width = '0%';
    loadingBar.style.display = 'block';
    
    loadingInterval = setInterval(() => {
        loadingProgress += Math.random() * 30;
        if (loadingProgress > 90) loadingProgress = 90;
        loadingBar.style.width = loadingProgress + '%';
    }, 200);
}

function stopLoading() {
    clearInterval(loadingInterval);
    loadingProgress = 100;
    loadingBar.style.width = '100%';
    
    setTimeout(() => {
        loadingBar.style.display = 'none';
    }, 400);
}

// Simulate loading on internal links
document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', () => {
        startLoading();
        setTimeout(stopLoading, 500);
    });
});

// ============================================
// ENHANCED SMOOTH SCROLL WITH OFFSET
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href !== '') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const offsetTop = target.offsetTop - 100; // Navbar height
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Update URL without jumping
                history.pushState(null, null, href);
            }
        }
    });
});

// ============================================
// IMAGE LAZY LOADING ENHANCEMENT
// ============================================
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[loading="lazy"]').forEach(img => {
        imageObserver.observe(img);
    });
}

// ============================================
// PERFORMANCE: REDUCE ANIMATIONS ON LOW-END DEVICES
// ============================================
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (prefersReducedMotion.matches) {
    document.querySelectorAll('*').forEach(el => {
        el.style.animation = 'none';
        el.style.transition = 'none';
    });
}

// ============================================
// VIEWPORT HEIGHT FIX FOR MOBILE
// ============================================
function setVH() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

setVH();
window.addEventListener('resize', setVH);

// ============================================
// CONSOLE EASTER EGG
// ============================================
console.log('%c🌿 Fundo Moraga - Batuco Off Road', 'font-size: 24px; font-weight: bold; color: #d4af37; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);');
console.log('%c475 años de historia desde 1551', 'font-size: 16px; color: #2c5530;');
console.log('%c¿Interesado en trabajar con nosotros? Envía tu CV a: contacto@fundomoraga.com', 'font-size: 14px; color: #666;');

// ============================================
// ANALYTICS READY
// ============================================
window.addEventListener('load', () => {
    // Track page load time
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`Página cargada en ${loadTime}ms`);
    
    // You can send this to your analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'timing_complete', {
            'name': 'load',
            'value': loadTime,
            'event_category': 'Performance'
        });
    }
});

// ============================================
// HISTORIA PAGE SPECIFIC
// ============================================

// Check if we're on historia page
if (window.location.pathname.includes('historia.html')) {
    
    // Auto-generate IDs for h2 headings
    const h2Elements = document.querySelectorAll('article h2');
    h2Elements.forEach((h2, index) => {
        if (!h2.id) {
            const text = h2.textContent;
            let id = '';
            
            // Create specific IDs based on heading text
            if (text.includes('Imperio Romano')) id = 'origenes-romanos';
            else if (text.includes('Cáceres')) id = 'caceres';
            else if (text.includes('Llegada') && text.includes('Chile')) id = 'llegada-chile';
            else if (text.includes('Curalaba')) id = 'curalaba';
            else if (text.includes('Transmisión Matrilineal')) id = 'transmision-matrilineal';
            else if (text.includes('Consolidación')) id = 'consolidacion';
            else if (text.includes('Hacienda') && text.includes('Chacabuco')) id = 'chacabuco';
            else if (text.includes('Te Deum') || text.includes('Independiente')) id = 'independencia';
            else if (text.includes('Rodeo')) id = 'rodeo';
            else if (text.includes('Unión') && text.includes('Linajes')) id = 'union-linajes';
            else if (text.includes('Toro-Zambrano')) id = 'toro-zambrano';
            else if (text.includes('Valle Central')) id = 'valle-central';
            else if (text.includes('Legado Militar') || text.includes('Artillería')) id = 'legado-militar';
            else if (text.includes('Contemporánea')) id = 'presencia-actual';
            else if (text.includes('Patrimonio')) id = 'patrimonio';
            else if (text.includes('Referencias')) id = 'referencias';
            else id = `seccion-${index}`;
            
            h2.id = id;
        }
    });
    
    // Animate images on scroll
    const images = document.querySelectorAll('.article-image');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                imageObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // Image lightbox for historia
    images.forEach(image => {
        image.addEventListener('click', () => {
            const lightbox = document.createElement('div');
            lightbox.className = 'lightbox active';
            lightbox.innerHTML = `
                <span class="lightbox-close">&times;</span>
                <img src="${image.src}" alt="${image.alt}">
                <div class="lightbox-caption">${image.alt}</div>
            `;
            
            document.body.appendChild(lightbox);
            document.body.style.overflow = 'hidden';
            
            // Close lightbox
            const closeBtn = lightbox.querySelector('.lightbox-close');
            closeBtn.addEventListener('click', () => {
                lightbox.classList.remove('active');
                document.body.style.overflow = 'auto';
                setTimeout(() => lightbox.remove(), 300);
            });
            
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox) {
                    lightbox.classList.remove('active');
                    document.body.style.overflow = 'auto';
                    setTimeout(() => lightbox.remove(), 300);
                }
            });
        });
    });
    
    // Smooth scroll for table of contents
    const tocLinks = document.querySelectorAll('.toc a');
    tocLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 100;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Highlight the section briefly
                targetElement.style.transition = 'background 0.5s ease';
                targetElement.style.background = 'rgba(212, 175, 55, 0.1)';
                targetElement.style.borderRadius = '8px';
                targetElement.style.padding = '10px';
                
                setTimeout(() => {
                    targetElement.style.background = '';
                    targetElement.style.padding = '';
                }, 2000);
            }
        });
    });
    
    // Active section highlighting in TOC
    const sections = document.querySelectorAll('article h2[id]');
    
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                tocLinks.forEach(link => {
                    link.style.color = '';
                    link.style.fontWeight = '';
                    
                    if (link.getAttribute('href') === `#${entry.target.id}`) {
                        link.style.color = 'var(--accent-color)';
                        link.style.fontWeight = '600';
                    }
                });
            }
        });
    }, {
        threshold: 0.5,
        rootMargin: '-100px 0px -70% 0px'
    });
    
    sections.forEach(section => sectionObserver.observe(section));
    
    // Animate paragraphs on scroll
    const paragraphs = document.querySelectorAll('article p');
    
    const paragraphObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateX(0)';
                }, 100);
                
                paragraphObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.3
    });
    
    paragraphs.forEach(p => paragraphObserver.observe(p));
    
    // Heading animations
    const headings = document.querySelectorAll('article h2, article h3');
    
    const headingObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(-20px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.7s cubic-bezier(0.4, 0, 0.2, 1)';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 50);
                
                headingObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.5
    });
    
    headings.forEach(h => headingObserver.observe(h));
    
    // Reading progress bar
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-color), #fbbf24);
        z-index: 9999;
        transition: width 0.1s ease;
        width: 0%;
    `;
    document.body.appendChild(progressBar);
    
    window.addEventListener('scroll', () => {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight - windowHeight;
        const scrolled = window.scrollY;
        const progress = (scrolled / documentHeight) * 100;
        progressBar.style.width = `${progress}%`;
    });
    
    // Print friendly version
    const printBtn = document.createElement('button');
    printBtn.innerHTML = '🖨️ Imprimir';
    printBtn.style.cssText = `
        position: fixed;
        bottom: 100px;
        right: 30px;
        background: white;
        color: var(--primary-color);
        border: 2px solid var(--accent-color);
        padding: 12px 24px;
        border-radius: 50px;
        cursor: pointer;
        font-weight: 600;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        z-index: 999;
        transition: all 0.3s ease;
        font-size: 14px;
    `;
    
    printBtn.addEventListener('mouseenter', () => {
        printBtn.style.background = 'var(--accent-color)';
        printBtn.style.color = 'black';
        printBtn.style.transform = 'translateY(-5px)';
        printBtn.style.boxShadow = '0 10px 30px rgba(212, 175, 55, 0.3)';
    });
    
    printBtn.addEventListener('mouseleave', () => {
        printBtn.style.background = 'white';
        printBtn.style.color = 'var(--primary-color)';
        printBtn.style.transform = 'translateY(0)';
        printBtn.style.boxShadow = '0 5px 20px rgba(0,0,0,0.1)';
    });
    
    printBtn.addEventListener('click', () => window.print());
    
    document.body.appendChild(printBtn);
    
    console.log('✅ Historia page enhancements loaded');
}
