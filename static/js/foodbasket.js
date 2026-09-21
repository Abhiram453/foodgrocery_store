/**
 * FoodBasket Vanilla JavaScript Micro-Interactions & Animation Suite
 * Zero external dependencies. Fast, accessible, lightweight.
 */

document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
  initAddToCartAnimation();
  initWishlistInteractions();
});

/* ── 1. Scroll Reveal IntersectionObserver ── */
function initScrollReveal() {
  const elements = document.querySelectorAll('.reveal-on-scroll');
  if (!elements.length) return;

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('reveal-visible');
          obs.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px'
    });

    elements.forEach(el => observer.observe(el));
  } else {
    // Fallback if IntersectionObserver not supported
    elements.forEach(el => el.classList.add('reveal-visible'));
  }
}

/* ── 2. Add To Cart Animation (Flying Thumbnail) ── */
function initAddToCartAnimation() {
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('form[action*="/cart/add/"]');
    if (!form) return;

    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // We enhance with AJAX + animation
    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnContent = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
    }

    const formData = new FormData(form);
    const actionUrl = form.action;

    try {
      const response = await fetch(actionUrl, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Find product card image for flying thumbnail animation
        const card = form.closest('.pcard, .detail-img-box') || document;
        const img = card.querySelector('img');
        const cartTarget = document.getElementById('cartBadge') || document.querySelector('.cart-btn-desktop') || document.querySelector('.mobile-cart-btn');

        if (!prefersReducedMotion && img && cartTarget) {
          animateFlyingThumbnail(img, cartTarget);
        }

        // Update cart badge
        updateCartBadge(data.cart_count);

        // Show toast
        showFbToast(data.message || 'Added to your basket!', 'success');
      } else {
        showFbToast(data.message || 'Unable to add item to basket.', 'error');
      }
    } catch (err) {
      console.warn('AJAX add to cart failed, falling back to form submit:', err);
      form.submit();
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnContent;
      }
    }
  });
}

function animateFlyingThumbnail(sourceImg, targetBadge) {
  const srcRect = sourceImg.getBoundingClientRect();
  const targetRect = targetBadge.getBoundingClientRect();

  const flyer = document.createElement('img');
  flyer.src = sourceImg.src;
  flyer.className = 'flying-thumb';
  flyer.style.width = '54px';
  flyer.style.height = '54px';
  flyer.style.left = `${srcRect.left + srcRect.width / 2 - 27}px`;
  flyer.style.top = `${srcRect.top + srcRect.height / 2 - 27}px`;
  flyer.style.opacity = '1';

  document.body.appendChild(flyer);

  // Trigger movement via requestAnimationFrame
  requestAnimationFrame(() => {
    flyer.style.left = `${targetRect.left + targetRect.width / 2 - 12}px`;
    flyer.style.top = `${targetRect.top + targetRect.height / 2 - 12}px`;
    flyer.style.width = '24px';
    flyer.style.height = '24px';
    flyer.style.opacity = '0.3';
  });

  setTimeout(() => {
    flyer.remove();
    targetBadge.classList.add('pulse');
    setTimeout(() => targetBadge.classList.remove('pulse'), 450);
  }, 650);
}

function updateCartBadge(count) {
  document.querySelectorAll('#cartBadge, .cart-badge, .mob-cart-badge').forEach(badge => {
    badge.textContent = count;
    badge.classList.remove('d-none');
    badge.classList.add('pulse');
    setTimeout(() => badge.classList.remove('pulse'), 450);
  });
}

/* ── 3. Wishlist Heart Pop Animation ── */
function initWishlistInteractions() {
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('form[action*="/wishlist/toggle/"]');
    if (!form) return;

    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const icon = btn ? btn.querySelector('i') : null;
    const formData = new FormData(form);

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        if (icon) {
          if (data.action === 'added') {
            icon.className = 'bi bi-heart-fill text-danger';
            btn.classList.add('pop');
            setTimeout(() => btn.classList.remove('pop'), 350);
          } else {
            icon.className = 'bi bi-heart text-muted';
          }
        }
        showFbToast(data.message, 'success');
      }
    } catch (err) {
      form.submit();
    }
  });
}

/* ── 4. Toast Notifications ── */
function showFbToast(message, type = 'success') {
  let container = document.getElementById('fbToastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'fbToastContainer';
    container.className = 'fb-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `fb-toast ${type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `
    <div class="d-flex align-items-center gap-2">
      <i class="bi ${type === 'error' ? 'bi-exclamation-circle-fill text-danger' : 'bi-check-circle-fill text-success'} fs-5"></i>
      <span>${message}</span>
    </div>
    <button type="button" class="btn-close btn-close-sm" style="font-size: 0.7rem;" aria-label="Close"></button>
  `;

  toast.querySelector('.btn-close').onclick = () => toast.remove();

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ── 5. Quantity Stepper Helper ── */
function stepQty(delta, inputId = 'qtyInput') {
  const input = document.getElementById(inputId);
  if (!input) return;

  const min = parseInt(input.getAttribute('min') || '1', 10);
  const max = parseInt(input.getAttribute('max') || '999', 10);
  let val = parseInt(input.value || '1', 10) + delta;

  if (val < min) val = min;
  if (val > max) val = max;

  input.value = val;
}
