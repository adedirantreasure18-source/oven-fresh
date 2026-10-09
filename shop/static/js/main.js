// ============================================
// OVEN FRESH - Interactive Animations
// ============================================

// Animated Background Canvas
const canvas = document.getElementById('bgCanvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let time = 0;

    const resize = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Create particles
    for (let i = 0; i < 60; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 3 + 1,
            speedX: (Math.random() - 0.5) * 0.3,
            speedY: -Math.random() * 0.8 - 0.2,
            opacity: Math.random() * 0.4 + 0.1,
            color: Math.random() > 0.5 ? '#D4A574' : '#8B2252'
        });
    }

    const animate = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        time += 0.01;

        // Gradient glow
        const gradient = ctx.createRadialGradient(
            canvas.width / 2 + Math.sin(time * 0.3) * 100,
            canvas.height / 2,
            0,
            canvas.width / 2, canvas.height / 2,
            canvas.width * 0.6
        );
        gradient.addColorStop(0, 'rgba(212, 165, 116, 0.08)');
        gradient.addColorStop(0.5, 'rgba(139, 34, 82, 0.04)');
        gradient.addColorStop(1, 'rgba(255, 248, 240, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Particles
        particles.forEach(p => {
            p.x += p.speedX + Math.sin(time + p.y * 0.01) * 0.3;
            p.y += p.speedY;

            if (p.y < -10) {
                p.y = canvas.height + 10;
                p.x = Math.random() * canvas.width;
            }
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.opacity;
            ctx.shadowColor = p.color;
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.globalAlpha = 1;
            ctx.shadowBlur = 0;
        });

        requestAnimationFrame(animate);
    };
    animate();
}

// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        if (window.scrollY > 400) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    }
});

// Back to top
const backToTopBtn = document.getElementById('backToTop');
if (backToTopBtn) {
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Mobile menu
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.toggle('active');
    });
    document.addEventListener('click', (e) => {
        if (!mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
            mobileMenu.classList.remove('active');
        }
    });
}

// Auto-hide messages
document.querySelectorAll('.message').forEach(msg => {
    setTimeout(() => {
        msg.style.animation = 'slideIn 0.4s ease reverse';
        setTimeout(() => msg.remove(), 400);
    }, 4000);
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Intersection Observer for animations
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.product-card, .feature-card, .preview-card, .analytics-card, .data-table-container').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Scroll-based fade-in for sections
document.querySelectorAll('.scroll-fade, section').forEach(el => {
    el.classList.add('scroll-fade');
    observer.observe(el);
});

// Parallax effect on hero
const hero = document.querySelector('.hero');
if (hero) {
    window.addEventListener('scroll', () => {
        const scrolled = window.scrollY;
        const heroContent = hero.querySelector('.hero-content');
        if (heroContent && scrolled < 600) {
            heroContent.style.transform = `translateY(${scrolled * 0.3}px)`;
            heroContent.style.opacity = 1 - (scrolled / 600);
        }
    });
}

// Tilt effect on product cards
document.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
    });
});

// Smooth count-up for stats
function animateValue(el, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    const step = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(start + range * easeOut);
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

// Button ripple effect
document.querySelectorAll('.btn, .action-btn, .add-btn, .filter-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        ripple.style.cssText = `position:absolute;width:0;height:0;border-radius:50%;background:rgba(255,255,255,0.4);transform:translate(-50%,-50%);pointer-events:none;`;
        ripple.style.left = (e.clientX - rect.left) + 'px';
        ripple.style.top = (e.clientY - rect.top) + 'px';
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        setTimeout(() => {
            ripple.style.transition = 'width 0.6s, height 0.6s, opacity 0.6s';
            ripple.style.width = '300px';
            ripple.style.height = '300px';
            ripple.style.opacity = '0';
        }, 10);
        setTimeout(() => ripple.remove(), 600);
    });
});

console.log('🥖 Oven Fresh loaded successfully!');

// AJAX Add to Cart
document.querySelectorAll('form[action*="cart/add"]').forEach(form => {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = this.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        btn.textContent = 'Adding...';
        btn.disabled = true;

        try {
            const formData = new FormData(this);
            const response = await fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrf_token'),
                }
            });
            const data = await response.json();

            if (data.login_required) {
                window.location.href = '/account/login/';
                return;
            }

            if (data.success) {
                // Update cart count in navbar
                document.querySelectorAll('.cart-count').forEach(el => {
                    el.textContent = data.cart_count;
                    el.style.transform = 'scale(1.3)';
                    setTimeout(() => el.style.transform = 'scale(1)', 300);
                });

                // Show success notification
                showNotification(data.message, 'success');

                // Button feedback
                btn.textContent = '✓ Added!';
                btn.style.background = '#4CAF50';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 1500);
            } else {
                showNotification(data.message || 'Something went wrong.', 'error');
                btn.textContent = originalText;
                btn.disabled = false;
            }
        } catch (err) {
            // Fallback: submit normally if AJAX fails
            this.submit();
        }
    });
});

// Notification system
function showNotification(message, type = 'success') {
    const container = document.querySelector('.messages-container') || createNotificationContainer();
    const notification = document.createElement('div');
    notification.className = `message message-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="message-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(notification);

    // Auto-remove after 4s
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.4s ease reverse';
        setTimeout(() => notification.remove(), 400);
    }, 4000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}