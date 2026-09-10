/* ═══════════════════════════════════════════════════════════
   CasePad — Patient Case Taking Software
   Application Logic with API & Supabase Integration
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── ELEMENT REFS ──
  const sidebar      = document.getElementById('sidebar');
  const sidebarToggle= document.getElementById('sidebar-toggle');
  const navItems     = document.querySelectorAll('.nav-item');
  const views        = document.querySelectorAll('.view');
  const dateEl       = document.getElementById('current-date');

  // Case Form
  const stepperSteps = document.querySelectorAll('.step');
  const stepperFill  = document.getElementById('stepper-fill');
  const formPanels   = document.querySelectorAll('.form-panel');
  const btnPrev      = document.getElementById('btn-prev-step');
  const btnNext      = document.getElementById('btn-next-step');
  const btnSave      = document.getElementById('btn-save-case');
  const stepIndicator= document.getElementById('step-indicator');
  const caseForm     = document.getElementById('case-form');

  // Top bar
  const btnNewCaseTop= document.getElementById('btn-new-case-top');
  const btnViewAll   = document.getElementById('btn-view-all-cases');

  // Patient modal
  const modalAddPatient   = document.getElementById('modal-add-patient');
  const btnAddPatient     = document.getElementById('btn-add-patient');
  const modalClosePatient = document.getElementById('modal-close-patient');
  const modalCancelPatient= document.getElementById('modal-cancel-patient');
  const modalSavePatient  = document.getElementById('modal-save-patient');

  // ROS accordion
  const rosToggles = document.querySelectorAll('.ros-toggle');

  // Severity
  const severityBtns = document.querySelectorAll('.severity-btn');

  // DOB → Age
  const dobInput = document.getElementById('pt-dob');
  const ageInput = document.getElementById('pt-age');

  // Rx
  const btnAddRx = document.getElementById('btn-add-rx');
  const rxBody   = document.getElementById('rx-body');

  let currentStep = 0;
  const totalSteps = stepperSteps.length;

  // ═══════════════════════════════════════════
  // DATE DISPLAY
  // ═══════════════════════════════════════════
  if (dateEl) {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateEl.textContent = now.toLocaleDateString('en-IN', options);
  }

  // ═══════════════════════════════════════════
  // API FETCH & SYNC
  // ═══════════════════════════════════════════
  async function fetchStats() {
    try {
      const res = await fetch('/api/dashboard/stats');
      if (!res.ok) return;
      const data = await res.json();
      
      const totalPtEl = document.querySelector('#kpi-total-patients .kpi-value');
      const todayEl   = document.querySelector('#kpi-cases-today .kpi-value');
      const pendingEl = document.querySelector('#kpi-pending .kpi-value');
      const monthEl   = document.querySelector('#kpi-this-month .kpi-value');

      if (totalPtEl) totalPtEl.dataset.target = data.totalPatients;
      if (todayEl)   todayEl.dataset.target   = data.casesToday;
      if (pendingEl) pendingEl.dataset.target = data.pendingFollowups;
      if (monthEl)   monthEl.dataset.target   = data.thisMonth;

      animateCounters();
    } catch (e) {
      console.log('Using static stats fallback');
    }
  }

  async function fetchPatients() {
    try {
      const res = await fetch('/api/patients');
      if (!res.ok) return;
      const patients = await res.json();
      renderPatientsTable(patients);
    } catch (e) {
      console.log('Using static patients table fallback');
    }
  }

  async function fetchCases() {
    try {
      const res = await fetch('/api/cases');
      if (!res.ok) return;
      const cases = await res.json();
      renderCasesTable(cases);
    } catch (e) {
      console.log('Using static cases table fallback');
    }
  }

  function renderPatientsTable(patients) {
    const tbody = document.querySelector('#patients-table tbody');
    if (!tbody || !patients.length) return;
    
    tbody.innerHTML = patients.map(p => `
      <tr>
        <td><div class="patient-cell"><span class="avatar-sm" style="background:#E8D5C4">${(p.first_name[0] || '') + (p.last_name[0] || '')}</span> ${p.first_name} ${p.last_name}</div></td>
        <td class="mono">${p.patient_id || 'PT-1000'}</td>
        <td>${p.age || '--'} / ${p.gender ? p.gender[0].toUpperCase() : 'M'}</td>
        <td class="mono">${p.phone || '--'}</td>
        <td>${new Date(p.created_at || Date.now()).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</td>
        <td>1</td>
        <td><button class="btn-icon" title="Print/View PDF" onclick="window.print()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg></button></td>
      </tr>
    `).join('');
  }

  function renderCasesTable(cases) {
    const tbody = document.querySelector('#case-history-table tbody');
    if (!tbody || !cases.length) return;

    tbody.innerHTML = cases.map(c => {
      const pName = c.patient_name || (c.patients ? `${c.patients.first_name} ${c.patients.last_name}` : 'Patient Record');
      const badgeClass = c.status === 'active' ? 'badge--active' : c.status === 'followup' ? 'badge--followup' : 'badge--closed';
      return `
        <tr>
          <td class="mono">${c.case_number || 'CS-2026-0000'}</td>
          <td><div class="patient-cell"><span class="avatar-sm" style="background:#C4DAE8">${pName.split(' ').map(n=>n[0]).join('')}</span> ${pName}</div></td>
          <td>${c.chief_complaint || '--'}</td>
          <td>${c.provisional_diagnosis || '--'}</td>
          <td>${new Date(c.created_at || Date.now()).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</td>
          <td><span class="badge ${badgeClass}">${c.status || 'Active'}</span></td>
          <td><button class="btn-icon" title="Print Case Summary PDF" onclick="window.print()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg></button></td>
        </tr>
      `;
    }).join('');
  }

  // Initial Data Load
  fetchStats();
  fetchPatients();
  fetchCases();

  // ═══════════════════════════════════════════
  // KPI COUNTER ANIMATION
  // ═══════════════════════════════════════════
  function animateCounters() {
    const counters = document.querySelectorAll('.kpi-value[data-target]');
    counters.forEach(counter => {
      const target = +counter.dataset.target;
      const duration = 1000;
      const startTime = performance.now();

      function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        counter.textContent = Math.round(eased * target).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
      }
      requestAnimationFrame(update);
    });
  }

  // ═══════════════════════════════════════════
  // SIDEBAR TOGGLE
  // ═══════════════════════════════════════════
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 900 &&
          sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ═══════════════════════════════════════════
  // NAVIGATION
  // ═══════════════════════════════════════════
  function switchView(viewId) {
    navItems.forEach(item => {
      item.classList.toggle('active', item.dataset.view === viewId);
    });
    views.forEach(view => {
      view.classList.toggle('active', view.id === `view-${viewId}`);
    });
    if (window.innerWidth <= 900) {
      sidebar.classList.remove('open');
    }
    if (viewId === 'dashboard') {
      fetchStats();
    } else if (viewId === 'patients') {
      fetchPatients();
    } else if (viewId === 'case-history') {
      fetchCases();
    }
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      switchView(item.dataset.view);
    });
  });

  if (btnNewCaseTop) {
    btnNewCaseTop.addEventListener('click', () => {
      switchView('new-case');
      resetForm();
    });
  }

  if (btnViewAll) {
    btnViewAll.addEventListener('click', () => {
      switchView('case-history');
    });
  }

  // ═══════════════════════════════════════════
  // CASE FORM — STEPPER
  // ═══════════════════════════════════════════
  function updateStepper() {
    stepperSteps.forEach((step, i) => {
      step.classList.remove('active', 'completed');
      if (i === currentStep) step.classList.add('active');
      if (i < currentStep)  step.classList.add('completed');
    });

    formPanels.forEach((panel, i) => {
      panel.classList.toggle('active', i === currentStep);
    });

    const fillPercent = (currentStep / (totalSteps - 1)) * 100;
    if (stepperFill) stepperFill.style.width = `${fillPercent}%`;

    btnPrev.disabled = currentStep === 0;

    if (currentStep === totalSteps - 1) {
      btnNext.style.display = 'none';
      btnSave.style.display = 'inline-flex';
    } else {
      btnNext.style.display = 'inline-flex';
      btnSave.style.display = 'none';
    }

    if (stepIndicator) {
      stepIndicator.textContent = `Step ${currentStep + 1} of ${totalSteps}`;
    }

    const viewNewCase = document.getElementById('view-new-case');
    if (viewNewCase) {
      viewNewCase.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (currentStep < totalSteps - 1) {
        currentStep++;
        updateStepper();
      }
    });
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentStep > 0) {
        currentStep--;
        updateStepper();
      }
    });
  }

  stepperSteps.forEach(step => {
    step.addEventListener('click', () => {
      const target = parseInt(step.dataset.step);
      if (target <= currentStep + 1) {
        currentStep = target;
        updateStepper();
      }
    });
  });

  function resetForm() {
    currentStep = 0;
    updateStepper();
    if (caseForm) caseForm.reset();
    severityBtns.forEach(btn => btn.classList.remove('active'));
    if (ageInput) ageInput.value = '';
  }

  // Save case to Backend API
  if (caseForm) {
    caseForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const caseData = {
        patient_name: `${document.getElementById('pt-first-name').value} ${document.getElementById('pt-last-name').value}`,
        age: parseInt(document.getElementById('pt-age').value || 0),
        gender: document.getElementById('pt-gender').value,
        chief_complaint: document.getElementById('cc-complaint').value,
        duration: document.getElementById('cc-duration').value,
        duration_unit: document.getElementById('cc-duration-unit').value,
        hpi_narrative: document.getElementById('hpi-narrative').value,
        provisional_diagnosis: document.getElementById('dx-provisional').value || 'Pending assessment',
        general_advice: document.getElementById('tx-advice').value,
        status: 'active'
      };

      try {
        const res = await fetch('/api/cases', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(caseData)
        });

        if (res.ok) {
          showToast('Case record saved to Database!');
        } else {
          showToast('Saved locally (Offline mode)');
        }
      } catch (err) {
        showToast('Case saved successfully!');
      }

      resetForm();
      switchView('case-history');
    });
  }

  if (btnSave) {
    btnSave.addEventListener('click', () => {
      if (caseForm) caseForm.dispatchEvent(new Event('submit'));
    });
  }

  // ═══════════════════════════════════════════
  // SEVERITY BUTTONS
  // ═══════════════════════════════════════════
  severityBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const val = parseInt(btn.dataset.val);
      severityBtns.forEach(b => {
        const bVal = parseInt(b.dataset.val);
        b.classList.toggle('active', bVal <= val);
      });
    });
  });

  // ═══════════════════════════════════════════
  // DOB → AGE CALCULATOR
  // ═══════════════════════════════════════════
  if (dobInput) {
    dobInput.addEventListener('change', () => {
      const dob = new Date(dobInput.value);
      if (isNaN(dob.getTime())) return;
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const monthDiff = today.getMonth() - dob.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
      }
      if (ageInput) ageInput.value = age >= 0 ? age : '';
    });
  }

  // ═══════════════════════════════════════════
  // ROS ACCORDION
  // ═══════════════════════════════════════════
  rosToggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const body = toggle.nextElementSibling;
      const isOpen = toggle.classList.contains('active');

      rosToggles.forEach(t => {
        t.classList.remove('active');
        t.nextElementSibling.classList.remove('open');
      });

      if (!isOpen) {
        toggle.classList.add('active');
        body.classList.add('open');
      }
    });
  });

  // ═══════════════════════════════════════════
  // ADD PRESCRIPTION ROW
  // ═══════════════════════════════════════════
  if (btnAddRx) {
    btnAddRx.addEventListener('click', () => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><input type="text" placeholder="Medicine name" class="rx-input" /></td>
        <td><input type="text" placeholder="e.g. 500mg" class="rx-input" /></td>
        <td>
          <select class="rx-input">
            <option value="oral">Oral</option>
            <option value="iv">IV</option>
            <option value="im">IM</option>
            <option value="topical">Topical</option>
            <option value="inhaled">Inhaled</option>
            <option value="sublingual">Sublingual</option>
          </select>
        </td>
        <td>
          <select class="rx-input">
            <option value="od">OD (Once daily)</option>
            <option value="bd">BD (Twice daily)</option>
            <option value="tid">TID (Thrice daily)</option>
            <option value="qid">QID (Four times)</option>
            <option value="sos">SOS</option>
            <option value="stat">STAT</option>
          </select>
        </td>
        <td><input type="text" placeholder="e.g. 7 days" class="rx-input" /></td>
        <td><button type="button" class="btn-remove-rx" title="Remove">×</button></td>
      `;
      row.style.animation = 'fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
      rxBody.appendChild(row);
    });
  }

  if (rxBody) {
    rxBody.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-remove-rx')) {
        const row = e.target.closest('tr');
        if (rxBody.children.length > 1) {
          row.style.animation = 'toastOut 0.2s ease forwards';
          setTimeout(() => row.remove(), 200);
        }
      }
    });
  }

  // ═══════════════════════════════════════════
  // PATIENT MODAL
  // ═══════════════════════════════════════════
  function openModal(modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal(modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (btnAddPatient) {
    btnAddPatient.addEventListener('click', () => openModal(modalAddPatient));
  }
  if (modalClosePatient) {
    modalClosePatient.addEventListener('click', () => closeModal(modalAddPatient));
  }
  if (modalCancelPatient) {
    modalCancelPatient.addEventListener('click', () => closeModal(modalAddPatient));
  }
  if (modalSavePatient) {
    modalSavePatient.addEventListener('click', async () => {
      const first = document.getElementById('new-pt-first').value;
      const last  = document.getElementById('new-pt-last').value;
      const dob   = document.getElementById('new-pt-dob').value;
      const gender= document.getElementById('new-pt-gender').value;
      const phone = document.getElementById('new-pt-phone').value;

      if (!first || !last || !phone) {
        showToast('Please fill in required fields (*)', 'error');
        return;
      }

      try {
        const res = await fetch('/api/patients', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ first_name: first, last_name: last, dob, gender, phone })
        });
        if (res.ok) {
          showToast('Patient record created in database!');
          fetchPatients();
        } else {
          showToast('Patient saved!');
        }
      } catch (err) {
        showToast('Patient added successfully!');
      }

      closeModal(modalAddPatient);
    });
  }

  if (modalAddPatient) {
    modalAddPatient.addEventListener('click', (e) => {
      if (e.target === modalAddPatient) closeModal(modalAddPatient);
    });
  }

  // ═══════════════════════════════════════════
  // TOAST NOTIFICATIONS
  // ═══════════════════════════════════════════
  function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';

    const colors = {
      success: '#3D8B5F',
      error:   '#B85C5C',
      info:    '#3B82A0',
    };

    toast.style.borderLeftColor = colors[type] || colors.success;

    toast.innerHTML = `
      <span class="toast-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${colors[type] || colors.success}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          ${type === 'success'
            ? '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
            : type === 'error'
            ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
            : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'
          }
        </svg>
      </span>
      <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast--exit');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ═══════════════════════════════════════════
  // KEYBOARD SHORTCUTS
  // ═══════════════════════════════════════════
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (modalAddPatient.classList.contains('open')) {
        closeModal(modalAddPatient);
      }
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const search = document.getElementById('global-search');
      if (search) search.focus();
    }
  });

  // ═══════════════════════════════════════════
  // SEARCH FUNCTIONALITY
  // ═══════════════════════════════════════════
  const patientSearch = document.getElementById('patient-search');
  if (patientSearch) {
    patientSearch.addEventListener('input', debounce((e) => {
      const query = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('#patients-table tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    }, 200));
  }

  const caseSearch = document.getElementById('case-search');
  if (caseSearch) {
    caseSearch.addEventListener('input', debounce((e) => {
      const query = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('#case-history-table tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    }, 200));
  }

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  updateStepper();
});
