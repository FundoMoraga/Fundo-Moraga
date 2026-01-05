// ============================================
// LEYENDA PAGE - ANIMATIONS & INTERACTIONS
// ============================================

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all story sections
document.addEventListener('DOMContentLoaded', () => {
    const sections = document.querySelectorAll('.story-section, .experience-section, .visit-section, .share-section, .back-home');
    sections.forEach(section => observer.observe(section));
});

// Mobile menu toggle
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');

mobileMenuToggle?.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    
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
        navLinks?.classList.remove('active');
        const spans = mobileMenuToggle?.querySelectorAll('span');
        spans?.forEach(span => {
            span.style.transform = '';
            span.style.opacity = '1';
        });
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Parallax effect for hero
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.leyenda-hero');
    if (hero && scrolled < window.innerHeight) {
        hero.style.transform = `translateY(${scrolled * 0.5}px)`;
        hero.style.opacity = 1 - (scrolled / window.innerHeight) * 0.8;
    }
});

// Share buttons functionality
const shareButtons = document.querySelectorAll('.share-btn');

shareButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        const url = encodeURIComponent(window.location.href);
        const title = encodeURIComponent('La Leyenda de la Loma del Diablo - Fundo Moraga');
        
        let shareUrl = '';
        
        if (btn.classList.contains('facebook')) {
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
        } else if (btn.classList.contains('twitter')) {
            shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
        } else if (btn.classList.contains('whatsapp')) {
            shareUrl = `https://wa.me/?text=${title}%20${url}`;
        }
        
        if (shareUrl) {
            window.open(shareUrl, '_blank', 'width=600,height=400');
        }
    });
});

// Add glow effect on scroll
let lastScroll = 0;
const navbar = document.querySelector('.dark-nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar?.style.setProperty('box-shadow', '0 5px 30px rgba(212, 175, 55, 0.2)');
    } else {
        navbar?.style.setProperty('box-shadow', 'none');
    }
    
    lastScroll = currentScroll;
});

// Easter egg: konami code for special effect
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-10);
    
    if (konamiCode.join(',') === konamiSequence.join(',')) {
        // Special effect: make the page more "devilish"
        document.body.style.animation = 'pulseRed 2s ease-in-out 3';
        setTimeout(() => {
            alert('🔥 Has descubierto el secreto de la Loma del Diablo... 🔥');
        }, 500);
    }
});

// Add pulse red animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulseRed {
        0%, 100% { filter: hue-rotate(0deg); }
        50% { filter: hue-rotate(30deg) saturate(2); }
    }
`;
document.head.appendChild(style);

// Console message
console.log('%c🔥 La Loma del Diablo te observa... 🔥', 'color: #d4af37; font-size: 20px; font-weight: bold; text-shadow: 0 0 10px rgba(212, 175, 55, 0.8);');
console.log('%cFundo Moraga - 475 años de historia', 'color: #c0c0c0; font-size: 14px;');
