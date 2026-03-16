/**
 * NexusFlow — JS Global
 * Gestão completa de clientes, agenda e atendimentos
 */

// ── DATA ATUAL ──
(function () {
  const el = document.getElementById('currentDate');
  if (el) {
    el.textContent = new Date().toLocaleDateString('pt-BR', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  }
})();

// ── SIDEBAR MOBILE ──
function openSidebar() {
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sidebarOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('sidebarOverlay')?.classList.remove('open');
  document.body.style.overflow = '';
}

// ── NOTIFICATION ──
function showNotification(msg, type = 'success') {
  const el = document.getElementById('notification');
  if (!el) return;

  const colors = {
    success: { bg: '#d1fae5', border: 'rgba(16,185,129,.3)', color: '#065f46' },
    danger:  { bg: '#fee2e2', border: 'rgba(239,68,68,.3)',  color: '#7f1d1d' },
    warning: { bg: '#fef3c7', border: 'rgba(245,158,11,.3)', color: '#78350f' },
    info:    { bg: '#dbeafe', border: 'rgba(59,130,246,.3)', color: '#1e40af' },
  };

  const c = colors[type] || colors.info;
  el.innerHTML = `
    <div style="
      background:${c.bg}; border:1px solid ${c.border}; color:${c.color};
      padding:12px 16px; border-radius:10px; font-size:13px; font-weight:500;
      box-shadow:0 8px 30px rgba(15,23,42,.15); min-width:260px;
      display:flex; align-items:center; gap:8px; font-family:'Plus Jakarta Sans',sans-serif;
    ">${msg}</div>`;

  el.classList.add('show');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 3500);
}

// ── MODAL HELPERS ──
function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

// ── FECHAR MODAL AO CLICAR FORA ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });

  // Swipe down para fechar (mobile)
  document.querySelectorAll('.modal').forEach(modal => {
    let startY = 0;
    modal.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
    modal.addEventListener('touchend', e => {
      const dy = e.changedTouches[0].clientY - startY;
      if (dy > 80 && modal.scrollTop === 0) {
        modal.closest('.modal-overlay')?.classList.remove('open');
      }
    }, { passive: true });
  });
});

// ── CONFIRMAR ORÇAMENTO ──
function confirmarOrcamento(id) {
  document.getElementById('confirmarOrcId').value = id;
  document.getElementById('confirmarData').value = '';
  document.getElementById('confirmarHora').value = '';
  openModal('modalConfirmar');
  setTimeout(() => document.getElementById('confirmarData')?.focus(), 300);
}

async function submitConfirmar() {
  const id   = document.getElementById('confirmarOrcId').value;
  const data = document.getElementById('confirmarData').value.trim();
  const hora = document.getElementById('confirmarHora').value.trim();

  if (!data || data.length < 10) {
    showNotification('Informe a data no formato DD/MM/AAAA', 'warning');
    document.getElementById('confirmarData').focus();
    return;
  }

  if (!hora || hora.length < 5) {
    showNotification('Informe o horário no formato HH:MM', 'warning');
    document.getElementById('confirmarHora').focus();
    return;
  }

  const btn = document.querySelector('#modalConfirmar .btn-primary');
  const originalText = btn.textContent;
  btn.textContent = 'Aguarde...';
  btn.disabled = true;

  try {
    const res  = await fetch(`/orcamentos/${id}/confirmar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data, hora }),
    });
    const json = await res.json();

    if (json.ok) {
      closeModal('modalConfirmar');
      showNotification('✓ Confirmado! Sessão adicionada à agenda.', 'success');
      setTimeout(() => location.reload(), 1600);
    } else {
      showNotification(json.error || 'Erro ao confirmar', 'danger');
    }
  } catch {
    showNotification('Erro de conexão. Tente novamente.', 'danger');
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

// ── MÁSCARAS ──
function maskData(input) {
  let v = input.value.replace(/\D/g, '');
  if (v.length > 2) v = v.slice(0, 2) + '/' + v.slice(2);
  if (v.length > 5) v = v.slice(0, 5) + '/' + v.slice(5);
  input.value = v.slice(0, 10);
}

function maskHora(input) {
  let v = input.value.replace(/\D/g, '');
  if (v.length > 2) v = v.slice(0, 2) + ':' + v.slice(2);
  input.value = v.slice(0, 5);
}

function maskPhone(input) {
  let v = input.value.replace(/\D/g, '');
  if (v.length > 2)  v = '(' + v.slice(0, 2) + ') ' + v.slice(2);
  if (v.length > 10) v = v.slice(0, 10) + '-' + v.slice(10);
  input.value = v.slice(0, 15);
}
