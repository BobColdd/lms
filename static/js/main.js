/* SFMCC LMS — main.js */

document.addEventListener('DOMContentLoaded', () => {

  // ── Flash message auto-dismiss ───────────────────────────
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.alert').style.display = 'none';
    });
  });
  setTimeout(() => {
    document.querySelectorAll('.alert.auto-dismiss').forEach(el => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    });
  }, 4000);

  // ── User dropdown ────────────────────────────────────────
  const userBtn = document.getElementById('userMenuBtn');
  const userMenu = document.getElementById('userMenu');
  if (userBtn && userMenu) {
    userBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userMenu.classList.toggle('open');
    });
    document.addEventListener('click', () => userMenu.classList.remove('open'));
  }

  // ── Mobile sidebar toggle ────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Confirm dialogs ──────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Active nav highlight ─────────────────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav a').forEach(link => {
    if (link.getAttribute('href') && path.startsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });

  // ── AJAX: Payment AJAX confirm ───────────────────────────
  document.querySelectorAll('.confirm-payment-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      if (!confirm('Confirm this payment? This will activate the enrollment.')) return;
      const form = this.closest('form');
      if (form) form.submit();
    });
  });

  // ── Progress bars animate on load ───────────────────────
  document.querySelectorAll('.progress-bar').forEach(bar => {
    const val = bar.dataset.value || 0;
    setTimeout(() => { bar.style.width = val + '%'; }, 200);
  });

});

/* ── Progress bar component ─────────────────────────────── */
function ProgressBar(el, value, color) {
  el.style.height = '8px';
  el.style.background = '#eaecee';
  el.style.borderRadius = '50px';
  el.style.overflow = 'hidden';
  const inner = document.createElement('div');
  inner.style.height = '100%';
  inner.style.width = '0';
  inner.style.background = color || 'var(--primary)';
  inner.style.borderRadius = '50px';
  inner.style.transition = 'width .6s ease';
  el.appendChild(inner);
  setTimeout(() => { inner.style.width = value + '%'; }, 300);
}

/* ── Number format helper ───────────────────────────────── */
function formatKES(amount) {
  return 'KES ' + parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2 });
}
