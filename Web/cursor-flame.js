/**
 * Cursor de Llama Personalizado - Fundo Moraga
 * Crea un cursor interactivo con forma de vela/llama encendida
 */

class FlameCursor {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.particles = [];
        this.isHovering = false;
        this.clickPower = 0;
        this.init();
    }

    init() {
        // Crear canvas para el cursor
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'flame-cursor';
        this.canvas.width = 60;
        this.canvas.height = 80;
        this.canvas.style.cssText = `
            position: fixed;
            pointer-events: none;
            z-index: 99999;
            top: 0;
            left: 0;
            will-change: transform;
        `;
        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        // Ocultar cursor por defecto
        document.body.style.cursor = 'none';

        // Event listeners
        document.addEventListener('mousemove', (e) => this.onMouseMove(e));
        document.addEventListener('mousedown', () => this.onMouseDown());
        document.addEventListener('mouseup', () => this.onMouseUp());
        document.addEventListener('mouseenter', () => this.onMouseEnter());
        document.addEventListener('mouseleave', () => this.onMouseLeave());

        // Detectar si está sobre elementos interactivos
        document.addEventListener('mouseover', (e) => {
            const target = e.target;
            this.isHovering = this.isInteractive(target);
        });

        this.animate();
    }

    isInteractive(element) {
        const interactiveTags = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
        return interactiveTags.includes(element.tagName) || 
               element.classList.contains('clickable') ||
               element.closest('button') ||
               element.closest('a');
    }

    onMouseMove(e) {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;

        // Generar partículas de fuego
        this.createFireParticles();
    }

    onMouseDown() {
        this.clickPower = 1;
    }

    onMouseUp() {
        this.clickPower = 0;
    }

    onMouseEnter() {
        this.canvas.style.display = 'block';
    }

    onMouseLeave() {
        this.canvas.style.display = 'none';
    }

    createFireParticles() {
        // Crear partículas ocasionalmente
        if (Math.random() > 0.7) {
            for (let i = 0; i < 2; i++) {
                this.particles.push({
                    x: this.mouseX + (Math.random() - 0.5) * 20,
                    y: this.mouseY + (Math.random() - 0.5) * 10,
                    vx: (Math.random() - 0.5) * 3,
                    vy: -Math.random() * 3 - 1,
                    life: 1,
                    size: Math.random() * 8 + 4,
                    hue: Math.random() * 60 + 15, // Naranja a rojo
                });
            }
        }
    }

    updateParticles() {
        this.particles = this.particles.filter(p => p.life > 0);
        
        this.particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy -= 0.1; // Gravedad inversa (suben)
            p.life -= 0.015;
            p.size *= 0.98;
        });
    }

    drawFlame() {
        const x = this.mouseX - this.canvas.width / 2;
        const y = this.mouseY - this.canvas.height / 2;

        this.canvas.style.transform = `translate(${x}px, ${y}px)`;

        // Limpiar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Dibujar glow
        this.drawGlow(centerX, centerY);

        // Dibujar núcleo de fuego (amarillo/blanco)
        this.drawFireCore(centerX, centerY);

        // Dibujar llama naranja
        this.drawFlameShape(centerX, centerY);

        // Dibujar chispa
        this.drawSpark(centerX, centerY);

        // Dibujar partículas
        this.drawParticles();
    }

    drawGlow(x, y) {
        const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, 25 + this.clickPower * 5);
        gradient.addColorStop(0, 'rgba(255, 180, 0, 0.4)');
        gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 25 + this.clickPower * 5, 0, Math.PI * 2);
        this.ctx.fill();
    }

    drawFireCore(x, y) {
        // Núcleo blanco
        const coreGradient = this.ctx.createRadialGradient(x, y, 0, x, y, 6);
        coreGradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
        coreGradient.addColorStop(1, 'rgba(255, 200, 100, 0.6)');
        
        this.ctx.fillStyle = coreGradient;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 6, 0, Math.PI * 2);
        this.ctx.fill();

        // Anillo amarillo
        const yellowGradient = this.ctx.createRadialGradient(x, y, 5, x, y, 12);
        yellowGradient.addColorStop(0, 'rgba(255, 200, 0, 0.8)');
        yellowGradient.addColorStop(1, 'rgba(255, 150, 0, 0.3)');
        
        this.ctx.fillStyle = yellowGradient;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 12, 0, Math.PI * 2);
        this.ctx.fill();
    }

    drawFlameShape(x, y) {
        const time = Date.now() * 0.003;
        const wave1 = Math.sin(time) * 3;
        const wave2 = Math.cos(time * 0.8) * 2;

        this.ctx.fillStyle = 'rgba(255, 100, 0, 0.7)';
        this.ctx.beginPath();
        
        // Forma de llama
        this.ctx.moveTo(x, y + 5);
        this.ctx.quadraticCurveTo(x - 6 + wave1, y - 10, x - 4, y - 20);
        this.ctx.quadraticCurveTo(x - 2, y - 28, x, y - 32 + wave2);
        this.ctx.quadraticCurveTo(x + 2, y - 28, x + 4, y - 20);
        this.ctx.quadraticCurveTo(x + 6 + wave1, y - 10, x, y + 5);
        this.ctx.closePath();
        this.ctx.fill();

        // Llama exterior (roja)
        this.ctx.fillStyle = 'rgba(255, 50, 0, 0.5)';
        this.ctx.beginPath();
        this.ctx.moveTo(x, y + 8);
        this.ctx.quadraticCurveTo(x - 8 + wave1, y - 12, x - 6, y - 25);
        this.ctx.quadraticCurveTo(x - 3, y - 32, x, y - 36 + wave2);
        this.ctx.quadraticCurveTo(x + 3, y - 32, x + 6, y - 25);
        this.ctx.quadraticCurveTo(x + 8 + wave1, y - 12, x, y + 8);
        this.ctx.closePath();
        this.ctx.fill();
    }

    drawSpark(x, y) {
        const sparkCount = 3;
        const time = Date.now() * 0.005;
        
        for (let i = 0; i < sparkCount; i++) {
            const angle = (i / sparkCount) * Math.PI * 2 + time;
            const distance = 15 + Math.sin(time + i) * 5;
            const sparkX = x + Math.cos(angle) * distance;
            const sparkY = y - 15 + Math.sin(angle) * distance;
            
            this.ctx.fillStyle = `rgba(255, 200, 0, ${Math.random() * 0.6 + 0.4})`;
            this.ctx.beginPath();
            this.ctx.arc(sparkX, sparkY, 1.5, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    drawParticles() {
        this.particles.forEach(p => {
            const relX = p.x - this.mouseX + this.canvas.width / 2;
            const relY = p.y - this.mouseY + this.canvas.height / 2;

            // Solo dibujar si está dentro del canvas
            if (relX > -10 && relX < this.canvas.width + 10 && 
                relY > -10 && relY < this.canvas.height + 10) {
                
                const hue = p.hue;
                this.ctx.fillStyle = `hsla(${hue}, 100%, 50%, ${p.life * 0.8})`;
                this.ctx.beginPath();
                this.ctx.arc(relX, relY, p.size, 0, Math.PI * 2);
                this.ctx.fill();
            }
        });
    }

    animate() {
        this.updateParticles();
        this.drawFlame();
        requestAnimationFrame(() => this.animate());
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new FlameCursor();
    });
} else {
    new FlameCursor();
}
