/**
 * MAIN APP CONTROLLER
 * Orchestrates dual-mode switching, theme management, offer stream filtering,
 * pagination, column sorting, sandbox scoring, dry-run simulation, and drawer details.
 */

// Application state for table pagination & sorting
const tableState = {
  currentPage: 1,
  pageSize: 25,
  sortField: 'score',
  sortAscending: false,
  activeFilterChip: 'all',
  lastFilteredOffers: []
};

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Theme (Dark Default or persisted in localStorage)
  try { initTheme(); } catch (e) { console.error('Theme init error:', e); }

  // 2. Setup 3-View Switcher & URL Hash IMMEDIATELY!
  // This guarantees that navigation buttons respond in < 1ms upon page load
  try {
    setupModeSwitcher();
    handleUrlHash();
    window.addEventListener('hashchange', handleUrlHash);
  } catch (e) {
    console.error('Mode switcher init error:', e);
  }

  // 3. Initialize Interactive Sound System
  try { initSoundSystem(); } catch (e) { console.warn('Sound init error:', e); }

  // 4. Setup Modern Card Spotlight & Welcome HUD Quick Actions
  try { setupSpotlightEffects(); } catch (e) {}
  try { setupWelcomeHudActions(); } catch (e) {}

  // 5. Setup Sticky Storyboard Process Scroll Animation
  try { setupStoryboardObserver(); } catch (e) {}

  // 6. Initialize Data Engine (Loads real offers or fallback)
  try {
    if (window.dataEngine) {
      await window.dataEngine.init();
      renderKpis();
      renderScraperHealth();
      renderDistributionStrip();
      renderOffersTable();
      setupFilterListeners();
      setupTableInteractions();
    }
  } catch (e) {
    console.error('DataEngine init error:', e);
  }

  // 7. Setup Scoring Sandbox with Live Input Debounce
  try { setupScoringSandbox(); } catch (e) {}

  // 8. Setup Email Generator & Multi-Step Dry-Run Simulator
  try { setupEmailPreviewer(); } catch (e) {}

  // 9. Initialize Interactive Terminal
  try {
    if (typeof TerminalEngine !== 'undefined') {
      const term = new TerminalEngine('terminal-output', 'terminal-input');
      term.init();
      window.terminalInstance = term;
    }
  } catch (e) {
    console.error('Terminal init error:', e);
  }

  // 10. Setup Drawer / Flyout Details
  try { setupDrawer(); } catch (e) {}
});

/* --------------------------------------------------------------------------
   THEME MANAGER
   -------------------------------------------------------------------------- */
function initTheme() {
  const savedTheme = localStorage.getItem('pfe_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('pfe_theme', next);
      updateThemeIcon(next);
      showToast('Thème mis à jour', `Mode ${next === 'dark' ? 'Cyber-Control sombre' : 'Executive clair'} activé.`);
    });
  }
}

function updateThemeIcon(theme) {
  const iconWrap = document.getElementById('theme-icon-wrap');
  if (!iconWrap) return;
  if (theme === 'dark') {
    iconWrap.innerHTML = `
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>`;
  } else {
    iconWrap.innerHTML = `
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>`;
  }
}

/* --------------------------------------------------------------------------
   3-VIEW UNIFIED SWITCHER (Home vs Dashboard vs Portfolio) & HISTORY SYNC
   -------------------------------------------------------------------------- */
function setupModeSwitcher() {
  const btnHome = document.getElementById('mode-btn-home');
  const btnMission = document.getElementById('mode-btn-mission');
  const btnPortfolio = document.getElementById('mode-btn-portfolio');
  const brandBtn = document.getElementById('brand-home-btn');

  const heroDashBtn = document.getElementById('hero-cta-dashboard-btn');
  const heroPortBtn = document.getElementById('hero-cta-portfolio-btn');
  const bridgeDashBtn = document.getElementById('bridge-dashboard-btn');
  const bridgePortBtn = document.getElementById('bridge-portfolio-btn');
  const heroBotBtn = document.getElementById('hero-view-bot-btn');
  const projectBotBtns = document.querySelectorAll('.project-btn-test-agent');

  if (btnHome) btnHome.addEventListener('click', () => switchMode('home'));
  if (btnMission) btnMission.addEventListener('click', () => switchMode('mission-control'));
  if (btnPortfolio) btnPortfolio.addEventListener('click', () => switchMode('portfolio'));

  if (heroDashBtn) heroDashBtn.addEventListener('click', () => switchMode('mission-control'));
  if (heroPortBtn) heroPortBtn.addEventListener('click', () => switchMode('portfolio'));
  if (bridgeDashBtn) bridgeDashBtn.addEventListener('click', () => switchMode('mission-control'));
  if (bridgePortBtn) bridgePortBtn.addEventListener('click', () => switchMode('portfolio'));

  if (brandBtn) {
    brandBtn.addEventListener('click', () => switchMode('home'));
    brandBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        switchMode('home');
      }
    });
  }
  if (heroBotBtn) {
    heroBotBtn.addEventListener('click', () => switchMode('mission-control'));
  }
  projectBotBtns.forEach(btn => {
    btn.addEventListener('click', () => switchMode('mission-control'));
  });
}

function switchMode(mode) {
  playSound('click');
  const homeView = document.getElementById('view-home');
  const missionView = document.getElementById('view-mission-control');
  const portfolioView = document.getElementById('view-portfolio');

  const btnHome = document.getElementById('mode-btn-home');
  const btnMission = document.getElementById('mode-btn-mission');
  const btnPortfolio = document.getElementById('mode-btn-portfolio');

  // Reset active classes on tabs
  [btnHome, btnMission, btnPortfolio].forEach(btn => {
    btn?.classList.remove('active');
    btn?.setAttribute('aria-selected', 'false');
  });

  // Hide all views first
  [homeView, missionView, portfolioView].forEach(v => {
    v?.classList.add('hidden');
    v?.classList.remove('view-enter');
  });

  if (mode === 'portfolio') {
    portfolioView?.classList.remove('hidden');
    portfolioView?.classList.add('view-enter');
    btnPortfolio?.classList.add('active');
    btnPortfolio?.setAttribute('aria-selected', 'true');
    if (window.location.hash !== '#portfolio') {
      window.location.hash = 'portfolio';
    }
  } else if (mode === 'mission-control' || mode === 'dashboard') {
    missionView?.classList.remove('hidden');
    missionView?.classList.add('view-enter');
    btnMission?.classList.add('active');
    btnMission?.setAttribute('aria-selected', 'true');
    if (window.location.hash !== '#dashboard') {
      window.location.hash = 'dashboard';
    }
  } else {
    // Default: Home View
    homeView?.classList.remove('hidden');
    homeView?.classList.add('view-enter');
    btnHome?.classList.add('active');
    btnHome?.setAttribute('aria-selected', 'true');
    if (window.location.hash !== '#accueil' && window.location.hash !== '') {
      window.location.hash = 'accueil';
    }
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleUrlHash() {
  const hash = window.location.hash.replace('#', '');
  if (hash === 'portfolio') {
    switchMode('portfolio');
  } else if (hash === 'dashboard' || hash === 'mission-control') {
    switchMode('mission-control');
  } else {
    switchMode('home');
  }
}

/* --------------------------------------------------------------------------
   STICKY STORYBOARD SCROLL-DRIVEN ANIMATION CONTROLLER
   -------------------------------------------------------------------------- */
const storyboardStepsData = {
  1: {
    tag: 'PHASE 1 / 4 · INGESTION',
    status: 'Actif (6/6)',
    statusClass: 'badge-success',
    title: '1. Collecte Multi-Sources',
    subtitle: 'Surveillance simultanée de 6 portails marocains avec rotation d\'User-Agents et respect des quotas anti-429.',
    metric1Val: '6 / 6',
    metric1Lbl: 'Portails Scrappés',
    metric2Val: '370+',
    metric2Lbl: 'Offres Traitées',
    iconSvg: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>'
  },
  2: {
    tag: 'PHASE 2 / 4 · AUDIT',
    status: 'Audit OK',
    statusClass: 'badge-warning',
    title: '2. Audit & Filtrage Sémantique',
    subtitle: 'Élimination des faux-positifs linguistiques ("j\'ai") et exclusion des profils seniors inadaptés au PFE.',
    metric1Val: '0',
    metric1Lbl: 'Faux-Positifs',
    metric2Val: '100%',
    metric2Lbl: 'Précision',
    iconSvg: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>'
  },
  3: {
    tag: 'PHASE 3 / 4 · SCORING',
    status: 'Calcul IA',
    statusClass: 'badge-success',
    title: '3. Qualification Sémantique IA',
    subtitle: 'Calcul d\'adéquation pondéré sur les compétences cibles (Python, Lakehouse, Airflow, Neo4j, RAG).',
    metric1Val: '71',
    metric1Lbl: 'Matchs ≥ 80%',
    metric2Val: '≥ 80%',
    metric2Lbl: 'Seuil Cible',
    iconSvg: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>'
  },
  4: {
    tag: 'PHASE 4 / 4 · DISPATCH',
    status: 'Prêt',
    statusClass: 'badge-indigo',
    title: '4. Match Recruteur & Dispatch',
    subtitle: 'Extraction des coordonnées RH, génération de candidature sur-mesure et simulation sécurisée en 3 étapes.',
    metric1Val: '100%',
    metric1Lbl: 'Dry-Run Validé',
    metric2Val: '0%',
    metric2Lbl: 'Risque Spam',
    iconSvg: '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>'
  }
};

let currentActiveStep = 1;

function setupStoryboardObserver() {
  const stepCards = document.querySelectorAll('.storyboard-step-card');
  if (stepCards.length === 0) return;

  // 1. Scroll listener using IntersectionObserver
  const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -50% 0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const stepNum = parseInt(entry.target.getAttribute('data-step'), 10);
        if (stepNum && stepNum !== currentActiveStep) {
          updateStoryboardStep(stepNum);
        }
      }
    });
  }, observerOptions);

  stepCards.forEach(card => observer.observe(card));

  // 2. Stepper Nav click interaction
  const navPills = document.querySelectorAll('.storyboard-progress-step-pill');
  navPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const targetStep = parseInt(pill.getAttribute('data-step-nav'), 10);
      const targetCard = document.querySelector(`.storyboard-step-card[data-step="${targetStep}"]`);
      if (targetCard) {
        playSound('click');
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });
}

function updateStoryboardStep(stepNum) {
  currentActiveStep = stepNum;
  const data = storyboardStepsData[stepNum];
  if (!data) return;

  // Update step cards active state
  document.querySelectorAll('.storyboard-step-card').forEach(c => {
    const s = parseInt(c.getAttribute('data-step'), 10);
    if (s === stepNum) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });

  // Update sticky progress pills
  document.querySelectorAll('.storyboard-progress-step-pill').forEach(p => {
    const s = parseInt(p.getAttribute('data-step-nav'), 10);
    if (s === stepNum) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });

  // Smoothly update HUD elements
  const tagEl = document.getElementById('sb-hud-step-tag');
  const statusEl = document.getElementById('sb-hud-status-badge');
  const iconEl = document.getElementById('sb-hud-icon');
  const titleEl = document.getElementById('sb-hud-title');
  const subtitleEl = document.getElementById('sb-hud-subtitle');
  const m1Val = document.getElementById('sb-metric-1-val');
  const m1Lbl = document.getElementById('sb-metric-1-lbl');
  const m2Val = document.getElementById('sb-metric-2-val');
  const m2Lbl = document.getElementById('sb-metric-2-lbl');

  if (tagEl) tagEl.textContent = data.tag;
  if (statusEl) {
    statusEl.textContent = data.status;
    statusEl.className = `badge ${data.statusClass}`;
  }
  if (iconEl) iconEl.innerHTML = data.iconSvg;
  if (titleEl) titleEl.textContent = data.title;
  if (subtitleEl) subtitleEl.textContent = data.subtitle;
  if (m1Val) m1Val.textContent = data.metric1Val;
  if (m1Lbl) m1Lbl.textContent = data.metric1Lbl;
  if (m2Val) m2Val.textContent = data.metric2Val;
  if (m2Lbl) m2Lbl.textContent = data.metric2Lbl;
}

/* --------------------------------------------------------------------------
   INTERACTIVE SOUND SYSTEM (Web Audio API Synthesizer - Zero Dependencies)
   -------------------------------------------------------------------------- */
let audioCtx = null;
let soundEnabled = localStorage.getItem('pfe_sound') === 'true';

function initSoundSystem() {
  updateSoundIcon(soundEnabled);
  const soundBtn = document.getElementById('sound-toggle-btn');
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      soundEnabled = !soundEnabled;
      localStorage.setItem('pfe_sound', soundEnabled.toString());
      updateSoundIcon(soundEnabled);
      if (soundEnabled) {
        playSound('pop');
        showToast('Effets sonores activés', 'Retour audio interactif opérationnel.');
      } else {
        showToast('Effets sonores désactivés', 'Mode silencieux actif.');
      }
    });
  }
}

function updateSoundIcon(enabled) {
  const wrap = document.getElementById('sound-icon-wrap');
  if (!wrap) return;
  if (enabled) {
    wrap.innerHTML = `
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      </svg>`;
  } else {
    wrap.innerHTML = `
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
      </svg>`;
  }
}

function playSound(type = 'click') {
  if (!soundEnabled) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (type === 'pop') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.08);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.08);
      osc.frequency.setValueAtTime(783.99, now + 0.16);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(300, now + 0.04);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.start(now);
      osc.stop(now + 0.04);
    }
  } catch (e) {
    // Audio Context blocked or unavailable
  }
}

/* --------------------------------------------------------------------------
   ANIMATED NUMBER COUNT-UP ENGINE
   -------------------------------------------------------------------------- */
function animateCountUp(el, endVal, duration = 900) {
  if (!el) return;
  const target = parseInt(endVal, 10);
  if (isNaN(target)) {
    el.textContent = endVal;
    return;
  }
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const currentVal = Math.floor(easeProgress * target);
    el.textContent = currentVal.toString();
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      el.textContent = target.toString();
      el.classList.add('count-updated');
      setTimeout(() => el.classList.remove('count-updated'), 400);
    }
  };
  window.requestAnimationFrame(step);
}

/* --------------------------------------------------------------------------
   SPOTLIGHT GLARE ENGINE (Linear / Apple Mouse-Follow Light)
   -------------------------------------------------------------------------- */
function setupSpotlightEffects() {
  document.addEventListener('pointermove', (e) => {
    const cards = document.querySelectorAll('.card, .kpi-card, .project-card, .cert-card, .welcome-hud-strip');
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}

/* --------------------------------------------------------------------------
   CELEBRATION CONFETTI ENGINE (Zero Dependencies Canvas Particle Burst)
   -------------------------------------------------------------------------- */
function triggerConfetti(originX, originY) {
  playSound('success');
  const canvas = document.getElementById('confetti-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const count = 75;
  const particles = [];
  const colors = ['#00e5ff', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#ffffff'];

  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 8 + 3;
    particles.push({
      x: originX || window.innerWidth / 2,
      y: originY || window.innerHeight / 3,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 4,
      size: Math.random() * 6 + 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1,
      decay: Math.random() * 0.02 + 0.012,
      rotation: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 12
    });
  }

  function frame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = false;
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.25;
      p.alpha -= p.decay;
      p.rotation += p.rotSpeed;

      if (p.alpha > 0) {
        alive = true;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        ctx.restore();
      }
    });

    if (alive) {
      requestAnimationFrame(frame);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
  requestAnimationFrame(frame);
}

/* --------------------------------------------------------------------------
   WELCOME HUD QUICK ACTIONS SETUP
   -------------------------------------------------------------------------- */
function setupWelcomeHudActions() {
  const btnHighMatch = document.getElementById('quick-high-match-btn');
  const btnSandbox = document.getElementById('quick-sandbox-btn');
  const btnPortfolio = document.getElementById('quick-portfolio-btn');
  const cvBtn = document.getElementById('header-cv-download-btn');

  if (btnHighMatch) {
    btnHighMatch.addEventListener('click', () => {
      playSound('click');
      const statusSelect = document.getElementById('filter-status-select');
      if (statusSelect) {
        statusSelect.value = 'high_match';
        tableState.currentPage = 1;
        renderOffersTable();
      }
      document.querySelector('.offer-explorer-card')?.scrollIntoView({ behavior: 'smooth' });
    });
  }

  if (btnSandbox) {
    btnSandbox.addEventListener('click', () => {
      playSound('click');
      const pfeAiBtn = document.querySelector('.preset-btn[data-preset="pfe_ai"]');
      if (pfeAiBtn) pfeAiBtn.click();
      document.querySelector('.scoring-sandbox')?.scrollIntoView({ behavior: 'smooth' });
    });
  }

  if (btnPortfolio) {
    btnPortfolio.addEventListener('click', () => {
      playSound('click');
      switchMode('portfolio');
    });
  }

  if (cvBtn) {
    cvBtn.addEventListener('click', () => {
      const rect = cvBtn.getBoundingClientRect();
      triggerConfetti(rect.left + rect.width / 2, rect.bottom);
      showToast('Téléchargement CV ATS', 'Le CV optimisé ATS d\'Anas Mouquine est en cours de téléchargement.');
    });
  }
}

/* --------------------------------------------------------------------------
   KPI METRICS RENDERING
   -------------------------------------------------------------------------- */
function renderKpis() {
  const stats = window.dataEngine.stats;
  const elTotal = document.getElementById('kpi-total-scraped');
  const elHighMatch = document.getElementById('kpi-high-match');
  const elRemunerated = document.getElementById('kpi-remunerated');
  const elDispatched = document.getElementById('kpi-dispatched');

  if (elTotal) animateCountUp(elTotal, stats.totalScraped, 800);
  if (elHighMatch) animateCountUp(elHighMatch, stats.highMatchCount, 950);
  if (elRemunerated) animateCountUp(elRemunerated, stats.remuneratedCount, 1050);
  if (elDispatched) animateCountUp(elDispatched, stats.dispatchedCount, 1150);
}

/* --------------------------------------------------------------------------
   DYNAMIC SCRAPER HEALTH MONITOR & DISTRIBUTION STRIP
   -------------------------------------------------------------------------- */
function renderScraperHealth() {
  const sources = window.dataEngine.stats.sourcesCount;
  const listEl = document.getElementById('scraper-health-list');
  if (!listEl || Object.keys(sources).length === 0) return;

  const sourceLabels = {
    dreamjob: 'DreamJob.ma',
    linkedin_guest: 'LinkedIn Guest',
    joblia: 'Joblia.ma',
    talent: 'Talent.com',
    rekrute: 'ReKrute.com',
    marocannonces: 'MarocAnnonces'
  };

  listEl.innerHTML = '';
  for (const [srcKey, count] of Object.entries(sources)) {
    const item = document.createElement('div');
    item.className = 'scraper-item';
    item.setAttribute('data-source', srcKey);
    item.title = `Filtrer par ${sourceLabels[srcKey] || srcKey}`;
    item.innerHTML = `
      <span class="scraper-name">${sourceLabels[srcKey] || srcKey}</span>
      <span class="scraper-status-text">${count} offres</span>
    `;
    item.addEventListener('click', () => {
      const select = document.getElementById('filter-source-select');
      if (select) {
        select.value = srcKey;
        tableState.currentPage = 1;
        renderOffersTable();
      }
    });
    listEl.appendChild(item);
  }
}

function renderDistributionStrip() {
  const stats = window.dataEngine.stats;
  const total = stats.totalScraped || 1;

  // Real distributions from dataset
  const highMatchCount = stats.highMatchCount; // >= 80%
  let mediumMatchCount = 0; // 60-79%
  let lowMatchCount = 0; // < 60%

  window.dataEngine.offers.forEach(o => {
    if (o.score >= 60 && o.score < 80) mediumMatchCount++;
    else if (o.score < 60) lowMatchCount++;
  });

  const pctHigh = Math.round((highMatchCount / total) * 100);
  const pctMed = Math.round((mediumMatchCount / total) * 100);
  const pctLow = Math.max(0, 100 - pctHigh - pctMed);

  const elPctHigh = document.getElementById('dist-pct-high');
  const elPctMed = document.getElementById('dist-pct-med');
  const elPctLow = document.getElementById('dist-pct-low');

  if (elPctHigh) elPctHigh.textContent = `${pctHigh}%`;
  if (elPctMed) elPctMed.textContent = `${pctMed}%`;
  if (elPctLow) elPctLow.textContent = `${pctLow}%`;

  const segHigh = document.getElementById('dist-seg-high');
  const segMed = document.getElementById('dist-seg-med');
  const segLow = document.getElementById('dist-seg-low');

  if (segHigh) {
    segHigh.style.width = `${pctHigh}%`;
    segHigh.title = `Match ≥ 80%: ${highMatchCount} offres (${pctHigh}%)`;
  }
  if (segMed) {
    segMed.style.width = `${pctMed}%`;
    segMed.title = `Match 60-79%: ${mediumMatchCount} offres (${pctMed}%)`;
  }
  if (segLow) {
    segLow.style.width = `${pctLow}%`;
    segLow.title = `Hors cible < 60%: ${lowMatchCount} offres (${pctLow}%)`;
  }

  // Populate dynamic source chips
  const sourcesContainer = document.getElementById('dist-sources-container');
  if (sourcesContainer && stats.sourcesCount) {
    const sourceLabels = {
      dreamjob: 'DreamJob.ma',
      linkedin_guest: 'LinkedIn Guest',
      joblia: 'Joblia.ma',
      talent: 'Talent.com',
      rekrute: 'ReKrute.com',
      marocannonces: 'MarocAnnonces'
    };

    sourcesContainer.innerHTML = '';
    for (const [srcKey, count] of Object.entries(stats.sourcesCount)) {
      const chip = document.createElement('span');
      chip.className = 'dist-source-chip';
      chip.setAttribute('data-source', srcKey);
      chip.title = `Filtrer par ${sourceLabels[srcKey] || srcKey}`;
      chip.innerHTML = `${sourceLabels[srcKey] || srcKey} : <strong>${count}</strong>`;
      chip.addEventListener('click', () => {
        const select = document.getElementById('filter-source-select');
        if (select) {
          select.value = srcKey;
          tableState.currentPage = 1;
          renderOffersTable();
        }
      });
      sourcesContainer.appendChild(chip);
    }

    const syncBadge = document.createElement('span');
    syncBadge.className = 'dist-source-chip dist-sync-status';
    syncBadge.innerHTML = '<span class="status-dot status-dot-active"></span> Pipeline sync OK';
    sourcesContainer.appendChild(syncBadge);
  }
}

/* --------------------------------------------------------------------------
   OFFERS TABLE RENDERING, PAGINATION & SORTING
   -------------------------------------------------------------------------- */
function renderOffersTable() {
  const tbody = document.getElementById('offers-table-body');
  const countBadge = document.getElementById('filtered-count-badge');
  if (!tbody) return;

  const keyword = document.getElementById('search-offers-input')?.value || '';
  const source = document.getElementById('filter-source-select')?.value || 'all';
  const status = document.getElementById('filter-status-select')?.value || 'all';
  const skillCategory = tableState.activeFilterChip;

  const filtered = window.dataEngine.filterOffers({ keyword, source, status, skillCategory });
  tableState.lastFilteredOffers = filtered;

  // CRITICAL FIX: Ensure #filtered-count-badge is ALWAYS updated before any early return!
  if (countBadge) {
    countBadge.textContent = `${filtered.length} offre(s)`;
  }

  tbody.innerHTML = '';

  // Zero results empty state
  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted" style="padding: 36px 14px;">
          <div style="font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 4px;">Aucune offre correspondante</div>
          <div>Modifiez vos mots-clés ou réinitialisez les filtres pour afficher des opportunités.</div>
        </td>
      </tr>
    `;
    updatePaginationControls(0, 1, 1, 0, 0);
    return;
  }

  // Sort offers
  const sorted = window.dataEngine.sortOffers(filtered, tableState.sortField, tableState.sortAscending);

  // Paginate offers
  const pageData = window.dataEngine.paginate(sorted, tableState.currentPage, tableState.pageSize);
  tableState.currentPage = pageData.currentPage;

  // Render rows
  pageData.items.forEach(offer => {
    const tr = document.createElement('tr');
    tr.className = 'offer-row';
    tr.addEventListener('click', () => openOfferDrawer(offer.id));

    // Badge Source
    const sourceBadge = `<span class="badge badge-neutral">${escapeHtml(offer.source.toUpperCase())}</span>`;

    // Status Badge
    let statusBadge = `<span class="badge badge-warning">EN ATTENTE</span>`;
    if (offer.applied) {
      statusBadge = `<span class="badge badge-indigo">DISPATCHÉ (DRY)</span>`;
    } else if (offer.is_remunerated) {
      statusBadge = `<span class="badge badge-cyan">RÉMUNÉRÉ</span>`;
    }

    // Score Color Style via semantic class
    let scoreColorClass = 'score-low';
    let scoreFillClass = 'bg-score-low';
    if (offer.score >= 80) {
      scoreColorClass = 'score-high';
      scoreFillClass = 'bg-score-high';
    } else if (offer.score >= 60) {
      scoreColorClass = 'score-medium';
      scoreFillClass = 'bg-score-medium';
    }

    tr.innerHTML = `
      <td class="offer-title-cell">
        <div class="offer-title-text" title="${escapeHtml(offer.title)}">${escapeHtml(offer.title)}</div>
        <div class="offer-company-sub">${escapeHtml(offer.company)} · ${escapeHtml(offer.location)}</div>
      </td>
      <td>${sourceBadge}</td>
      <td>
        <div class="score-bar-wrapper">
          <div class="score-bar-track">
            <div class="score-bar-fill ${scoreFillClass}" style="width: ${offer.score}%;"></div>
          </div>
          <span class="score-num ${scoreColorClass}">${offer.score}%</span>
        </div>
      </td>
      <td>${statusBadge}</td>
      <td class="text-right">
        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openOfferDrawer('${offer.id}')">
          Examiner
        </button>
      </td>
    `;

    tbody.appendChild(tr);
  });

  updatePaginationControls(pageData.total, pageData.currentPage, pageData.totalPages, pageData.startIndex, pageData.endIndex);
}

function updatePaginationControls(total, currentPage, totalPages, startIdx, endIdx) {
  const infoEl = document.getElementById('pagination-info');
  const indicatorEl = document.getElementById('pagination-page-indicator');
  const prevBtn = document.getElementById('btn-prev-page');
  const nextBtn = document.getElementById('btn-next-page');

  if (infoEl) {
    if (total === 0) {
      infoEl.textContent = '0 offre affichée';
    } else {
      infoEl.textContent = `Affichage ${startIdx}–${endIdx} sur ${total} offres`;
    }
  }

  if (indicatorEl) {
    indicatorEl.textContent = `Page ${currentPage} / ${totalPages}`;
  }

  if (prevBtn) {
    prevBtn.disabled = currentPage <= 1;
  }

  if (nextBtn) {
    nextBtn.disabled = currentPage >= totalPages;
  }
}

function setupFilterListeners() {
  const searchInput = document.getElementById('search-offers-input');
  const sourceSelect = document.getElementById('filter-source-select');
  const statusSelect = document.getElementById('filter-status-select');
  const filterChips = document.querySelectorAll('.filter-chip');

  searchInput?.addEventListener('input', debounce(() => {
    tableState.currentPage = 1;
    renderOffersTable();
  }, 200));

  sourceSelect?.addEventListener('change', () => {
    tableState.currentPage = 1;
    renderOffersTable();
  });

  statusSelect?.addEventListener('change', () => {
    tableState.currentPage = 1;
    renderOffersTable();
  });

  // Quick Filter Chips Handling with real dataset categories
  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const filterType = chip.getAttribute('data-filter');
      tableState.activeFilterChip = filterType;
      tableState.currentPage = 1;

      if (filterType === 'all') {
        if (searchInput) searchInput.value = '';
        if (statusSelect) statusSelect.value = 'all';
        if (sourceSelect) sourceSelect.value = 'all';
      } else if (filterType === 'high_match') {
        if (statusSelect) statusSelect.value = 'high_match';
      } else if (filterType === 'remunerated') {
        if (statusSelect) statusSelect.value = 'remunerated';
      }

      renderOffersTable();
    });
  });

  // Global Keyboard Shortcut (Cmd+K / Ctrl+K or /)
  window.addEventListener('keydown', (e) => {
    const isCmdK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k';
    const isSlash = e.key === '/' && document.activeElement !== searchInput && document.activeElement.tagName !== 'TEXTAREA';

    if (isCmdK || isSlash) {
      e.preventDefault();
      // If portfolio mode is active, focus terminal; otherwise focus search
      const portfolioView = document.getElementById('view-portfolio');
      if (portfolioView && !portfolioView.classList.contains('hidden')) {
        const termInput = document.getElementById('terminal-input');
        termInput?.focus();
        termInput?.select();
      } else {
        searchInput?.focus();
        searchInput?.select();
      }
    }
  });
}

function setupTableInteractions() {
  // Pagination buttons
  const prevBtn = document.getElementById('btn-prev-page');
  const nextBtn = document.getElementById('btn-next-page');

  prevBtn?.addEventListener('click', () => {
    if (tableState.currentPage > 1) {
      tableState.currentPage--;
      renderOffersTable();
      document.querySelector('.offer-table-wrapper')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  nextBtn?.addEventListener('click', () => {
    tableState.currentPage++;
    renderOffersTable();
    document.querySelector('.offer-table-wrapper')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // Sortable column headers
  const sortHeaders = document.querySelectorAll('.sortable-th');
  sortHeaders.forEach(th => {
    th.addEventListener('click', () => {
      const field = th.getAttribute('data-sort');
      if (tableState.sortField === field) {
        tableState.sortAscending = !tableState.sortAscending;
      } else {
        tableState.sortField = field;
        tableState.sortAscending = field === 'title' || field === 'source';
      }

      // Update sort icons
      sortHeaders.forEach(h => {
        const icon = h.querySelector('.sort-icon');
        if (icon) {
          if (h === th) {
            icon.textContent = tableState.sortAscending ? '▲' : '▼';
            icon.style.opacity = '1';
          } else {
            icon.textContent = '↕';
            icon.style.opacity = '0.6';
          }
        }
      });

      renderOffersTable();
    });
  });
}

/* --------------------------------------------------------------------------
   DRAWER / INSPECT DETAILS FLYOUT
   -------------------------------------------------------------------------- */
function setupDrawer() {
  const backdrop = document.getElementById('drawer-backdrop');
  const drawer = document.getElementById('drawer-flyout');
  const closeBtn = document.getElementById('drawer-close-btn');

  function close() {
    backdrop?.classList.remove('active');
    drawer?.classList.remove('active');
  }

  backdrop?.addEventListener('click', close);
  closeBtn?.addEventListener('click', close);
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}

function openOfferDrawer(id) {
  const offer = window.dataEngine.getOfferById(id);
  if (!offer) return;

  const backdrop = document.getElementById('drawer-backdrop');
  const drawer = document.getElementById('drawer-flyout');

  // Populate drawer fields
  document.getElementById('drawer-offer-title').textContent = offer.title;
  document.getElementById('drawer-offer-company').textContent = `${offer.company} · ${offer.location}`;
  document.getElementById('drawer-offer-score').textContent = `${offer.score}%`;
  document.getElementById('drawer-offer-source').textContent = offer.source.toUpperCase();

  // Recruiter Intel
  const emailBox = document.getElementById('drawer-recruiter-email');
  if (offer.contact_email) {
    emailBox.innerHTML = `
      <a href="mailto:${offer.contact_email}" class="btn btn-primary btn-sm" target="_blank">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
        ${offer.contact_email}
      </a>`;
  } else {
    emailBox.innerHTML = `<span class="text-muted text-xs">Aucun email direct dans l'annonce publique</span>`;
  }

  const linkedinBox = document.getElementById('drawer-recruiter-linkedin');
  if (offer.hr_linkedin_url || offer.linkedin_url) {
    const targetUrl = offer.hr_linkedin_url || offer.linkedin_url;
    linkedinBox.innerHTML = `
      <a href="${targetUrl}" class="btn btn-outline btn-sm" target="_blank">
        <svg fill="currentColor" viewBox="0 0 24 24" class="social-btn-icon"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
        ${offer.hr_name ? `Contacter ${offer.hr_name}` : 'Voir Profil Recruteur'}
      </a>`;
  } else {
    linkedinBox.innerHTML = `<span class="text-muted text-xs">Profil LinkedIn personnel non indexé</span>`;
  }

  // Offer link
  const urlRow = document.getElementById('drawer-offer-url-row');
  if (urlRow) {
    if (offer.url && offer.url !== '#') {
      urlRow.innerHTML = `
        <a href="${offer.url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
          Consulter l'Offre Source (${offer.source})
        </a>`;
    } else {
      urlRow.innerHTML = '';
    }
  }

  // Skills chips
  const skillsContainer = document.getElementById('drawer-skills-chips');
  skillsContainer.innerHTML = '';
  offer.matched_skills.forEach(skill => {
    const chip = document.createElement('span');
    chip.className = 'skill-chip skill-chip-detected';
    chip.textContent = skill;
    skillsContainer.appendChild(chip);
  });

  // Action Apply Preview in Drawer
  const previewBtn = document.getElementById('drawer-preview-application-btn');
  if (previewBtn) {
    previewBtn.onclick = () => {
      drawer?.classList.remove('active');
      backdrop?.classList.remove('active');
      loadOfferIntoEmailPreview(offer);
      document.getElementById('email-preview-section')?.scrollIntoView({ behavior: 'smooth' });
    };
  }

  backdrop?.classList.add('active');
  drawer?.classList.add('active');
}

/* --------------------------------------------------------------------------
   AI SCORING SANDBOX (PLAYGROUND) WITH LIVE DEBOUNCE
   -------------------------------------------------------------------------- */
function setupScoringSandbox() {
  const textarea = document.getElementById('sandbox-input-textarea');
  const runBtn = document.getElementById('sandbox-run-btn');

  const presets = {
    pfe_ai: "Entreprise : AI Innovate Casablanca\nIntitulé : Stage PFE - Ingénieur RAG & Agents Autonomes\nMissions : Conception de pipelines RAG sémantiques avec LangChain, Python et FastAPI. Modélisation de bases vectorielles et benchmarks LLM. Stage de fin d'études conventionné rémunéré (gratification mensuelle).",
    data_lakehouse: "Entreprise : FinTech Services Maroc\nIntitulé : Stage PFE Data Engineer (Airflow / Kafka)\nProfil recherché : Élève-ingénieur en 5ème année. Maîtrise de Python, SQL, Apache Airflow (création de DAGs), ingestion temps réel avec Apache Kafka et conteneurisation Docker. Stage rémunéré pré-embauche.",
    senior_excluded: "Société : Global Consulting Rabat\nIntitulé : Lead Data Architect (CDI Confirmé - 7+ ans d'expérience)\nExigences : Minimum 7 ans d'ancienneté dans la gestion de clusters Hadoop/Spark. Encadrement d'équipe et direction technique.",
    homonym_ia: "Annonce : J'ai besoin d'un rédacteur web pour articles de blog généralistes. Télétravail occasionnel. Début immédiat."
  };

  // Wire preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-preset');
      if (presets[key] && textarea) {
        textarea.value = presets[key];
        runScoringEvaluation();
      }
    });
  });

  // Live input debounce scoring as user types
  textarea?.addEventListener('input', debounce(() => {
    if (textarea.value.trim().length >= 15) {
      runScoringEvaluation();
    }
  }, 250));

  runBtn?.addEventListener('click', runScoringEvaluation);
}

function runScoringEvaluation() {
  const textarea = document.getElementById('sandbox-input-textarea');
  const text = textarea?.value || '';

  const result = window.scoringEngine.evaluateOfferText(text);

  // Update UI Result
  const scoreNum = document.getElementById('sandbox-score-number');
  const verdictBadge = document.getElementById('sandbox-verdict-badge');
  const reasoningText = document.getElementById('sandbox-reasoning-text');
  const detectedChips = document.getElementById('sandbox-detected-skills');
  const missingChips = document.getElementById('sandbox-missing-skills');
  const exclusionsBox = document.getElementById('sandbox-exclusions-list');

  if (scoreNum) scoreNum.textContent = result.score.toString();
  if (verdictBadge) {
    verdictBadge.textContent = result.verdict;
    verdictBadge.className = `badge ${result.badgeClass}`;
  }
  if (reasoningText) reasoningText.textContent = result.reasoning;

  if (detectedChips) {
    detectedChips.innerHTML = '';
    if (result.detectedSkills.length === 0) {
      detectedChips.innerHTML = '<span class="text-muted text-xs">Aucune compétence clé détectée</span>';
    } else {
      result.detectedSkills.forEach(skill => {
        const span = document.createElement('span');
        span.className = 'skill-chip skill-chip-detected';
        span.textContent = `✓ ${skill}`;
        detectedChips.appendChild(span);
      });
    }
  }

  if (missingChips) {
    missingChips.innerHTML = '';
    if (result.missingSkills.length === 0) {
      missingChips.innerHTML = '<span class="text-muted text-xs">Profil 100% complet</span>';
    } else {
      result.missingSkills.forEach(skill => {
        const span = document.createElement('span');
        span.className = 'skill-chip skill-chip-missing';
        span.textContent = `— ${skill}`;
        missingChips.appendChild(span);
      });
    }
  }

  if (exclusionsBox) {
    exclusionsBox.innerHTML = '';
    if (result.exclusions.length === 0) {
      exclusionsBox.innerHTML = '<span class="text-success text-xs">✓ Aucun facteur de blocage détecté</span>';
    } else {
      result.exclusions.forEach(exc => {
        const div = document.createElement('div');
        div.className = 'text-danger text-xs';
        div.textContent = `⚠ ${exc}`;
        exclusionsBox.appendChild(div);
      });
    }
  }
}

/* --------------------------------------------------------------------------
   EMAIL GENERATOR & DRY-RUN PREVIEWER WITH ANIMATED SIMULATION PIPELINE
   -------------------------------------------------------------------------- */
function setupEmailPreviewer() {
  const btnHtml = document.getElementById('tab-btn-html');
  const btnPlain = document.getElementById('tab-btn-plain');
  const htmlView = document.getElementById('email-html-view');
  const plainView = document.getElementById('email-plain-view');
  const dryRunBtn = document.getElementById('btn-dry-run-dispatch');
  const pipelineEl = document.getElementById('dry-run-simulation-pipeline');

  btnHtml?.addEventListener('click', () => {
    btnHtml.classList.add('active');
    btnHtml.setAttribute('aria-selected', 'true');
    btnPlain?.classList.remove('active');
    btnPlain?.setAttribute('aria-selected', 'false');
    htmlView?.classList.remove('hidden');
    plainView?.classList.add('hidden');
  });

  btnPlain?.addEventListener('click', () => {
    btnPlain.classList.add('active');
    btnPlain?.setAttribute('aria-selected', 'true');
    btnHtml?.classList.remove('active');
    btnHtml?.setAttribute('aria-selected', 'false');
    plainView?.classList.remove('hidden');
    htmlView?.classList.add('hidden');
  });

  dryRunBtn?.addEventListener('click', async () => {
    if (pipelineEl) {
      pipelineEl.classList.remove('hidden');
      const step1 = document.getElementById('step-sim-1');
      const step2 = document.getElementById('step-sim-2');
      const step3 = document.getElementById('step-sim-3');

      // Reset steps
      [step1, step2, step3].forEach(s => {
        s?.classList.remove('active', 'completed');
      });

      // Step 1: Validation
      step1?.classList.add('active');
      await delay(450);
      step1?.classList.remove('active');
      step1?.classList.add('completed');

      // Step 2: Packaging
      step2?.classList.add('active');
      await delay(450);
      step2?.classList.remove('active');
      step2?.classList.add('completed');

      // Step 3: Dispatch & Recording
      step3?.classList.add('active');
      await delay(450);
      step3?.classList.remove('active');
      step3?.classList.add('completed');
    }

    if (dryRunBtn) {
      const rect = dryRunBtn.getBoundingClientRect();
      triggerConfetti(rect.left + rect.width / 2, rect.top);
    }

    showToast(
      'Simulation Dry-Run Réussie',
      'Candidature personnalisée préparée et consignée dans applied_offers.json (Aucun envoi réel en mode sécurisé).'
    );
  });
}

function loadOfferIntoEmailPreview(offer) {
  const companyEl = document.getElementById('email-preview-company');
  const subjectEl = document.getElementById('email-preview-subject');
  const htmlView = document.getElementById('email-html-view');
  const plainView = document.getElementById('email-plain-view');

  const roleTitle = offer.title || 'Stage PFE IA & Data Engineering';
  const companyName = offer.company || 'Entreprise Partenaire';
  const contactName = offer.hr_name ? `Mme/M. ${offer.hr_name}` : "l'équipe Recrutement";
  const skillsList = offer.matched_skills && offer.matched_skills.length ? offer.matched_skills.join(', ') : 'Python, IA, Data Engineering';

  if (companyEl) companyEl.textContent = companyName;
  if (subjectEl) subjectEl.textContent = `Candidature Stage PFE (${offer.title}) – Anas MOUQUINE – ${companyName}`;

  if (htmlView) {
    htmlView.innerHTML = `
      <p><strong>À l'attention de ${escapeHtml(contactName)} · <span id="email-preview-company">${escapeHtml(companyName)}</span></strong></p>
      <p>Madame, Monsieur,</p>
      <p>Actuellement en 5<sup>e</sup> année du cycle d'ingénieur d'État en <strong>Intelligence Artificielle &amp; Génie des Données à l'EMSI Casablanca</strong>, je vous soumets ma candidature pour l'opportunité de <strong>${escapeHtml(roleTitle)}</strong> au sein de vos équipes.</p>
      <p>Passionné par la mise en production de pipelines de données distribués et de systèmes multi-agents, j'ai développé des compétences approfondies sur <em>${escapeHtml(skillsList)}</em>.</p>
      <p>Vous trouverez ci-joint mon <strong>CV ATS</strong> détaillant mes projets et mes certifications Google, HKUST et Meta.</p>
      <p>Cordialement,<br><strong>Anas MOUQUINE</strong><br><small>+212 672-104126 · anasmouqine@gmail.com</small></p>
    `;
  }

  if (plainView) {
    plainView.textContent = `Objet: Candidature Stage PFE (${roleTitle}) - Anas MOUQUINE - ${companyName}

À l'attention de ${contactName},

Élève-ingénieur en 5e année à l'EMSI Casablanca (spécialité IA & Data Engineering), je vous propose ma candidature pour votre opportunité de stage : ${roleTitle}.

Compétences alignées avec votre besoin : ${skillsList}.

Pièce jointe : cv_ats_pfe.pdf
Portfolio : anasmouquinee.github.io/port/
LinkedIn : linkedin.com/in/anas-mouqine-329207304/

Anas MOUQUINE
+212 672-104126`;
  }

  showToast('Candidature Générée', `Le modèle de courriel et le CV ATS ont été personnalisés pour ${companyName}.`);
}

/* --------------------------------------------------------------------------
   TOAST NOTIFICATION HELPER
   -------------------------------------------------------------------------- */
function showToast(title, message) {
  playSound('pop');
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast active';
  toast.innerHTML = `
    <div class="toast-icon">
      <svg fill="none" viewBox="0 0 24 24" stroke="var(--accent-cyan)">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('active');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(str) {
  if (!str) return '';
  return str.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
