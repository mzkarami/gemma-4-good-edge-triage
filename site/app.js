const state = { data: null, selected: null };

const $ = (selector) => document.querySelector(selector);
const fmtLatency = (ms) => `${ms.toFixed(2)} ms`;
const fmtF1 = (value) => value.toFixed(4);

async function loadData() {
  const response = await fetch('data.json');
  if (!response.ok) throw new Error('Could not load demo data');
  state.data = await response.json();
  const captureMode = new URLSearchParams(window.location.search).get('capture');
  if (captureMode === 'volunteer' || captureMode === 'optimization') {
    document.body.dataset.capture = captureMode;
  }
  if (document.querySelector('[data-volunteer-console]')) {
    initVolunteerConsole();
    return;
  }
  bindModeSwitching();
  bindUploadDemo();
  renderSamples();
  renderFrontier();
  renderExperiments();
  const initialSampleId = new URLSearchParams(window.location.search).get('sample') || state.data.samples[0].id;
  selectSample(initialSampleId);
  const initialMode = captureMode === 'optimization' || window.location.hash === '#optimization' ? 'optimization' : 'volunteer';
  showMode(initialMode, { scroll: window.location.hash === '#volunteer' || window.location.hash === '#optimization' });
}

function bindModeSwitching() {
  document.querySelectorAll('[data-mode-target]').forEach((control) => {
    control.addEventListener('click', (event) => {
      const mode = control.dataset.modeTarget;
      if (!mode) return;
      event.preventDefault();
      showMode(mode, { scroll: true });
    });
  });
}

function showMode(mode, { scroll } = { scroll: false }) {
  document.querySelectorAll('[data-mode-section]').forEach((section) => {
    section.classList.toggle('hidden', section.dataset.modeSection !== mode);
  });
  document.querySelectorAll('.mode-button').forEach((button) => {
    const active = button.dataset.modeTarget === mode;
    button.classList.toggle('active', active);
    button.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  const section = document.querySelector(`[data-mode-section="${mode}"]`);
  if (section) {
    history.replaceState(null, '', `#${mode}`);
    if (scroll) {
      section.scrollIntoView({ behavior: 'auto', block: 'start' });
      window.setTimeout(() => section.scrollIntoView({ behavior: 'auto', block: 'start' }), 250);
    }
  }
}

function bindUploadDemo() {
  const form = $('#upload-form');
  const input = $('#demo-image');
  const runButton = $('#run-upload-demo');
  const modeInputs = document.querySelectorAll('input[name="inference-mode"]');
  if (!form || !input) return;

  const selectedInferenceMode = () => document.querySelector('input[name="inference-mode"]:checked')?.value || 'static';
  const updateInferenceMode = () => {
    const live = selectedInferenceMode() === 'live';
    const liveInputs = $('#live-inputs');
    const curatedScenarios = $('#curated-scenarios');
    liveInputs?.classList.toggle('hidden', !live);
    if (liveInputs) liveInputs.hidden = !live;
    curatedScenarios?.classList.toggle('hidden', live);
    if (curatedScenarios) curatedScenarios.hidden = live;
    runButton.textContent = 'Run Live Gemma preview';
    $('#simulation-status').textContent = live
      ? 'Live Gemma preview selected: paste the judge token from the Kaggle submission notes. Images are capped at 25 MB and sanitized server-side.'
      : 'Curated showcase selected: click a scenario below. No upload, backend request, or new model call is needed for these prepared product examples.';
    $('#simulation-status').classList.remove('complete', 'error');
  };

  modeInputs.forEach((radio) => radio.addEventListener('change', updateInferenceMode));
  updateInferenceMode();

  $('#judge-token')?.addEventListener('input', () => setTokenError());

  input.addEventListener('change', () => {
    const file = input.files?.[0];
    $('#file-name').textContent = file ? file.name : 'No file selected';
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      setSimulationStatus('Image must be 25 MB or smaller.', 'error');
      input.value = '';
      $('#file-name').textContent = 'No file selected';
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      $('#image-hint').innerHTML = `<img class="preview-image" src="${reader.result}" alt="Uploaded disaster example preview" />`;
    };
    reader.readAsDataURL(file);
  });

  const runUpload = async (event) => {
    event.preventDefault();
    if (selectedInferenceMode() === 'live') {
      await runLiveInference(input);
    } else {
      setSimulationStatus('Curated showcase uses the scenario buttons below; no upload or new model call is needed.');
    }
  };

  form.addEventListener('submit', runUpload);
  runButton?.addEventListener('click', runUpload);
}

function setSimulationStatus(message, tone = 'complete') {
  const status = $('#simulation-status');
  status.textContent = message;
  status.classList.remove('complete', 'error');
  status.classList.add(tone);
}

function setTokenError(message = '') {
  const tokenInput = $('#judge-token');
  const error = $('#judge-token-error');
  if (!error) return;
  error.textContent = message;
  error.hidden = !message;
  tokenInput?.setAttribute('aria-invalid', message ? 'true' : 'false');
}

function pulseTriageCard() {
  $('.triage-card').classList.add('just-updated');
  window.setTimeout(() => $('.triage-card')?.classList.remove('just-updated'), 900);
}

async function runLiveInference(input) {
  const file = input.files?.[0];
  const note = $('#demo-report').value.trim();
  const token = $('#judge-token').value.trim();
  const endpoint = '/api/triage';
  setTokenError();
  if (!file) {
    setSimulationStatus('Live Gemma preview needs an image upload.', 'error');
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    setSimulationStatus('Image must be 25 MB or smaller.', 'error');
    return;
  }
  if (!token) {
    setTokenError('Use the judge token from the Kaggle submission notes.');
    $('#judge-token')?.focus();
    return;
  }

  const formData = new FormData();
  formData.append('image', file);
  formData.append('note', note);
  setSimulationStatus('Running Live Gemma preview…', 'complete');

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'X-Judge-Token': token },
      body: formData
    });
    if (!response.ok) {
      const friendly = await friendlyLiveError(response);
      if (response.status === 401 || response.status === 403) {
        setTokenError(friendly);
        $('#judge-token')?.focus();
      } else {
        setSimulationStatus(friendly, 'error');
      }
      return;
    }
    const result = await response.json();
    renderLiveResult(result, note, file.name);
    setSimulationStatus(`Live Gemma preview complete: ${result.label.replaceAll('_', ' ')} · ${result.priority}.`);
    pulseTriageCard();
  } catch (error) {
    console.error(error);
    setSimulationStatus('Live model unavailable; curated showcase is still usable.', 'error');
  }
}

function renderLiveResult(result, note, fileName) {
  state.selected = result;
  document.querySelectorAll('.sample-button').forEach((button) => button.classList.remove('active'));
  $('#selected-mode').textContent = result.mode || 'Live Gemma preview';
  $('#sample-title').textContent = `Live upload: ${fileName}`;
  $('#sample-report').textContent = note || 'No field note supplied; Live Gemma preview used the uploaded image only.';
  $('#result-label').textContent = result.label;
  $('#result-priority').textContent = result.priority;
  $('#result-latency').textContent = fmtLatency(Number(result.latency_ms || 0));
  $('#result-action').textContent = result.next_action;
  const source = result.live_model ? 'Live Gemma 4 vision' : 'Guarded API fallback';
  const summary = result.scene_summary || 'No scene summary returned.';
  $('#result-reason-label').textContent = source;
  $('#result-reason').textContent = `${summary} ${result.disclaimer}`;
}

async function friendlyLiveError(response) {
  if (response.status === 401 || response.status === 403) return 'Use the judge token from the Kaggle submission notes.';
  if (response.status === 413) return 'Image must be 25 MB or smaller.';
  if (response.status === 415) return 'Use a JPEG, PNG, or WebP image.';
  if (response.status === 429) return 'Rate limit hit; try again shortly. The curated showcase is still usable.';
  if (response.status === 503) return 'Live model unavailable; curated showcase is still usable.';
  try {
    const body = await response.json();
    return body.detail || 'Live Gemma preview failed; curated showcase is still usable.';
  } catch (_) {
    return 'Live Gemma preview failed; curated showcase is still usable.';
  }
}

function renderSamples() {
  const list = $('#sample-list');
  list.innerHTML = '';
  for (const sample of state.data.samples) {
    const button = document.createElement('button');
    button.className = 'sample-button';
    button.type = 'button';
    button.dataset.id = sample.id;
    button.innerHTML = `<strong>${sample.title}</strong><span>${sample.label.replaceAll('_', ' ')}</span>`;
    button.addEventListener('click', () => selectSample(sample.id));
    list.appendChild(button);
  }
}

function selectSample(id) {
  const sample = state.data.samples.find((item) => item.id === id) || state.data.samples[0];
  state.selected = sample;
  document.querySelectorAll('.sample-button').forEach((button) => {
    button.classList.toggle('active', button.dataset.id === sample.id);
  });

  $('#selected-mode').textContent = sample.mode;
  renderScenarioImage(sample);
  $('#sample-title').textContent = sample.title;
  $('#sample-report').textContent = sample.report;
  $('#result-label').textContent = sample.label;
  $('#result-priority').textContent = sample.priority;
  $('#result-latency').textContent = fmtLatency(sample.latencyMs);
  $('#result-action').textContent = sample.nextAction;
  $('#result-reason-label').textContent = sample.confidence || 'Image scan';
  $('#result-reason').textContent = sample.reason;
}

function renderScenarioImage(sample) {
  const imageHint = $('#image-hint');
  if (sample.imageSrc) {
    imageHint.innerHTML = `<img class="preview-image" src="${sample.imageSrc}" alt="${sample.imageAlt || sample.imageHint}" />`;
  } else {
    imageHint.textContent = sample.imageHint;
  }
}

function renderFrontier() {
  const grid = $('#frontier-grid');
  grid.innerHTML = '';
  for (const profile of state.data.frontier) {
    const card = document.createElement('article');
    card.className = 'frontier-card';
    const speedWidth = Math.max(8, Math.min(100, 100 - (profile.latencyMs / 4000) * 100));
    card.innerHTML = `
      <span class="card-kicker">${profile.status.toUpperCase()} · ${profile.samples} samples</span>
      <h3>${profile.profile}</h3>
      <span class="big-number">${fmtF1(profile.f1)}</span>
      <div class="bar" aria-label="Latency headroom under 4 second budget"><span style="width:${speedWidth}%"></span></div>
      <p class="muted">${profile.useCase}</p>
      <p><span class="decision">Latency:</span> ${fmtLatency(profile.latencyMs)}</p>
      <p class="muted small">Run: ${profile.run}</p>
    `;
    grid.appendChild(card);
  }

  const context = document.createElement('article');
  context.className = 'frontier-card';
  context.innerHTML = `
    <span class="card-kicker">FIELD BUDGET</span>
    <h3>4,000 ms ceiling</h3>
    <span class="big-number">&lt; 0.3s</span>
    <p class="muted">Both public profiles stay far below the mission-critical limit, preserving time for human decision-making.</p>
    <p><span class="decision">Strategy:</span> choose speed for volume; choose accuracy for critical review.</p>
  `;
  grid.appendChild(context);
}

function renderExperiments() {
  const board = $('#experiment-board');
  board.innerHTML = '';
  for (const experiment of state.data.experiments) {
    const card = document.createElement('article');
    card.className = 'experiment-card';
    const isWinner = experiment.id.includes('480');
    card.innerHTML = `
      <span class="card-kicker">${experiment.id}</span>
      <h3>${experiment.label}</h3>
      <p class="muted small">Technical note: ${experiment.technicalLabel || experiment.id}</p>
      <p><span class="decision">F1:</span> ${fmtF1(experiment.f1)} · <span class="decision">Latency:</span> ${fmtLatency(experiment.latencyMs)}</p>
      <p class="decision" style="color:${isWinner ? 'var(--green)' : 'var(--warning)'}">${experiment.decision}</p>
      <p><span class="decision">What changed:</span> ${experiment.change || experiment.label}</p>
      <p class="muted">${experiment.detail}</p>
    `;
    board.appendChild(card);
  }
}

function initVolunteerConsole() {
  const form = $('#field-console-form');
  const reportInput = $('#field-report');
  const imageInput = $('#field-image');
  const audioInput = $('#field-audio');
  const status = $('#field-console-status');
  const bridgeButton = $('#load-bridge-example');
  if (!form || !reportInput) return;

  const bridgeSample = state.data?.samples?.find((sample) => sample.id === 'bridge-flood') || state.data?.samples?.[0];
  const saveDraft = () => {
    const draft = {
      report: reportInput.value,
      imageName: imageInput?.files?.[0]?.name || '',
      audioName: audioInput?.files?.[0]?.name || '',
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem('edge-triage-field-draft', JSON.stringify(draft));
    $('#draft-status').textContent = 'Draft saved locally';
  };
  const updateFileName = (input, target, emptyLabel) => {
    if (!input || !target) return;
    target.textContent = input.files?.[0]?.name || emptyLabel;
  };
  const renderFieldResult = (sample, report) => {
    const title = report.split(/[.!?]/).find(Boolean)?.trim() || sample.title || 'Field report';
    $('#app-result-title').textContent = title;
    $('#app-result-summary').textContent = 'Edge-Triage converted the field note into a triage card that can be reviewed before coordinator handoff.';
    $('#app-result-label').textContent = sample.label;
    $('#app-result-priority').textContent = sample.priority;
    $('#app-result-latency').textContent = fmtLatency(sample.latencyMs);
    $('#app-result-action').textContent = sample.nextAction;
    $('#app-handoff').textContent = 'Queued for coordinator sync when connectivity returns. Human review required before operational decisions.';
    $('#phone-report-title').textContent = title;
    $('#phone-report-note').textContent = report;
    $('#phone-priority').textContent = sample.priority;
    status.textContent = 'Queued for coordinator sync. Human review required before action.';
    status.classList.add('complete');
    status.classList.remove('error');
  };

  reportInput.addEventListener('input', saveDraft);
  imageInput?.addEventListener('change', () => {
    updateFileName(imageInput, $('#field-image-name'), 'No image selected');
    saveDraft();
  });
  audioInput?.addEventListener('change', () => {
    updateFileName(audioInput, $('#field-audio-name'), 'No audio selected');
    saveDraft();
  });
  bridgeButton?.addEventListener('click', () => {
    reportInput.value = 'Bridge washed out after flood. Road blocked. No injuries visible. Need routing guidance.';
    saveDraft();
    renderFieldResult(bridgeSample, reportInput.value);
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const report = reportInput.value.trim();
    if (!report) {
      status.textContent = 'Add a short field report before running Edge-Triage.';
      status.classList.add('error');
      status.classList.remove('complete');
      reportInput.focus();
      return;
    }
    saveDraft();
    renderFieldResult(bridgeSample, report);
  });
  saveDraft();
}

loadData().catch((error) => {
  console.error(error);
  document.body.insertAdjacentHTML('afterbegin', `<div style="padding:1rem;background:#3f1d1d;color:white">${error.message}</div>`);
});
