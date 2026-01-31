// Blog Scripts - Fundo Moraga
// Version 1.0.0 - 2026-01-31

(() => {
    'use strict';
    
    // ============================================
    // DARK MODE TOGGLE
    // ============================================
    const darkModeToggle = document.getElementById('darkModeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    document.body.setAttribute('data-theme', currentTheme);
    
    darkModeToggle?.addEventListener('click', () => {
        const theme = document.body.getAttribute('data-theme');
        const newTheme = theme === 'light' ? 'dark' : 'light';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        const icon = darkModeToggle.querySelector('svg');
        if (newTheme === 'dark') {
            icon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
        } else {
            icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
        }
    });
    
    // ============================================
    // CATEGORY FILTER
    // ============================================
    const filterBtns = document.querySelectorAll('.filter-btn');
    const blogCards = document.querySelectorAll('.blog-card');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.getAttribute('data-category');
            
            // Update active button
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter cards
            blogCards.forEach(card => {
                if (category === 'all' || card.getAttribute('data-category') === category) {
                    card.style.display = 'block';
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 10);
                } else {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
    
    // ============================================
    // SEARCH FUNCTIONALITY
    // ============================================
    const blogSearch = document.getElementById('blogSearch');
    
    const normalizeText = (text) => {
        return text.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    };
    
    blogSearch?.addEventListener('input', (e) => {
        const query = normalizeText(e.target.value);
        
        blogCards.forEach(card => {
            const title = card.querySelector('h3')?.textContent || '';
            const excerpt = card.querySelector('p')?.textContent || '';
            const category = card.querySelector('.post-category-badge')?.textContent || '';
            
            const searchText = normalizeText(`${title} ${excerpt} ${category}`);
            
            if (searchText.includes(query)) {
                card.style.display = 'block';
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 10);
            } else {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.display = 'none';
                }, 300);
            }
        });
        
        // If empty search, reset to current filter
        if (!query) {
            const activeFilter = document.querySelector('.filter-btn.active');
            if (activeFilter) {
                activeFilter.click();
            }
        }
    });
    
    // ============================================
    // LOAD MORE FUNCTIONALITY
    // ============================================
    let currentPage = 1;
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    
    loadMoreBtn?.addEventListener('click', () => {
        loadMoreBtn.textContent = 'Cargando...';
        loadMoreBtn.disabled = true;
        
        // Simulate API call
        setTimeout(() => {
            // In production, this would fetch more posts from API
            console.log('Loading more posts...');
            currentPage++;
            
            loadMoreBtn.textContent = 'Cargar más artículos';
            loadMoreBtn.disabled = false;
            
            // Hide button if no more posts (example)
            if (currentPage >= 3) {
                loadMoreBtn.style.display = 'none';
            }
        }, 1000);
    });
    
    // ============================================
    // NEWSLETTER FORM
    // ============================================
    const newsletterForm = document.getElementById('newsletterForm');
    
    newsletterForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = newsletterForm.querySelector('input[type="email"]').value;
        const submitBtn = newsletterForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        submitBtn.textContent = 'Suscribiendo...';
        submitBtn.disabled = true;
        
        try {
            // In production, send to newsletter API
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Show success message
            const successMsg = document.createElement('p');
            successMsg.className = 'newsletter-success';
            successMsg.textContent = '¡Suscripción exitosa! Revisa tu correo.';
            successMsg.style.color = '#4ade80';
            successMsg.style.marginTop = '15px';
            successMsg.style.fontWeight = '600';
            
            newsletterForm.parentElement.appendChild(successMsg);
            newsletterForm.reset();
            
            setTimeout(() => {
                successMsg.remove();
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }, 3000);
            
        } catch (error) {
            console.error('Newsletter subscription error:', error);
            submitBtn.textContent = 'Error - Reintentar';
            
            setTimeout(() => {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }, 2000);
        }
    });
    
    // ============================================
    // MOBILE MENU TOGGLE
    // ============================================
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    mobileMenuToggle?.addEventListener('click', () => {
        const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
        
        mobileMenuToggle.setAttribute('aria-expanded', !isExpanded);
        navLinks?.classList.toggle('active');
        
        // Animate hamburger
        const spans = mobileMenuToggle.querySelectorAll('span');
        if (!isExpanded) {
            spans[0].style.transform = 'rotate(45deg) translate(7px, 7px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
        } else {
            spans.forEach(span => {
                span.style.transform = '';
                span.style.opacity = '1';
            });
        }
    });
    
    // ============================================
    // SCROLL TO TOP
    // ============================================
    const scrollToTop = document.getElementById('scrollToTop');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            scrollToTop?.classList.add('visible');
        } else {
            scrollToTop?.classList.remove('visible');
        }
    });
    
    scrollToTop?.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // ============================================
    // SMOOTH SCROLL FOR ANCHORS
    // ============================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                const yOffset = -80; // Navbar height
                const y = target.getBoundingClientRect().top + window.pageYOffset + yOffset;
                
                window.scrollTo({
                    top: y,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // ============================================
    // LAZY LOADING IMAGES
    // ============================================
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // If it has data-src, load it
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // ============================================
    // READING PROGRESS BAR (for article pages)
    // ============================================
    const createReadingProgress = () => {
        const article = document.querySelector('article');
        if (!article) return;
        
        const progressBar = document.createElement('div');
        progressBar.className = 'reading-progress-bar';
        progressBar.innerHTML = '<div class="reading-progress-fill"></div>';
        document.body.appendChild(progressBar);
        
        window.addEventListener('scroll', () => {
            const articleTop = article.offsetTop;
            const articleHeight = article.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrollTop = window.scrollY;
            
            const progress = ((scrollTop - articleTop + windowHeight) / articleHeight) * 100;
            const clampedProgress = Math.min(Math.max(progress, 0), 100);
            
            const fill = progressBar.querySelector('.reading-progress-fill');
            fill.style.width = clampedProgress + '%';
        });
    };
    
    // ============================================
    // SHARE BUTTONS (for article pages)
    // ============================================
    const initShareButtons = () => {
        const shareButtons = document.querySelectorAll('[data-share]');
        
        shareButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                const platform = btn.getAttribute('data-share');
                const url = encodeURIComponent(window.location.href);
                const title = encodeURIComponent(document.title);
                
                let shareUrl = '';
                
                switch (platform) {
                    case 'facebook':
                        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                        break;
                    case 'twitter':
                        shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                        break;
                    case 'linkedin':
                        shareUrl = `https://www.linkedin.com/shareArticle?mini=true&url=${url}&title=${title}`;
                        break;
                    case 'whatsapp':
                        shareUrl = `https://wa.me/?text=${title}%20${url}`;
                        break;
                }
                
                if (shareUrl) {
                    window.open(shareUrl, '_blank', 'noopener,noreferrer,width=600,height=500');
                }
            });
        });
    };
    
    // Initialize
    createReadingProgress();
    initShareButtons();
    
    console.log('✅ Blog scripts loaded successfully');
})();
