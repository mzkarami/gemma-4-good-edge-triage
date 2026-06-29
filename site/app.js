const state = { data: null, selected: null };

const $ = (selector) => document.querySelector(selector);
const fmtLatency = (ms) => `${ms.toFixed(2)} ms`;
const fmtF1 = (value) => value.toFixed(4);

function textElement(tag, text, className = '') {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function appendText(parent, tag, text, className = '') {
  const element = textElement(tag, text, className);
  parent.appendChild(element);
  return element;
}

function replaceWithImage(container, src, alt, className = '') {
  if (!container) return;
  const image = document.createElement('img');
  if (className) image.className = className;
  image.src = src;
  image.alt = alt;
  container.replaceChildren(image);
}

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
      ? 'Live Gemma preview selected: images are capped at 25 MB, sanitized server-side, and protected by backend rate limits.'
      : 'Curated showcase selected: click a scenario below. No upload, backend request, or new model call is needed for these prepared product examples.';
    $('#simulation-status').classList.remove('complete', 'error');
  };

  modeInputs.forEach((radio) => radio.addEventListener('change', updateInferenceMode));
  updateInferenceMode();


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
      replaceWithImage($('#image-hint'), String(reader.result), 'Uploaded disaster example preview', 'preview-image');
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


function pulseTriageCard() {
  $('.triage-card').classList.add('just-updated');
  window.setTimeout(() => $('.triage-card')?.classList.remove('just-updated'), 900);
}

async function runLiveInference(input) {
  const file = input.files?.[0];
  const note = $('#demo-report').value.trim();
  const endpoint = '/api/triage';
  if (!file) {
    setSimulationStatus('Live Gemma preview needs an image upload.', 'error');
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    setSimulationStatus('Image must be 25 MB or smaller.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('image', file);
  formData.append('note', note);
  setSimulationStatus('Running Live Gemma preview…', 'complete');

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      const friendly = await friendlyLiveError(response);
      setSimulationStatus(friendly, 'error');
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
  if (response.status === 401 || response.status === 403) return 'Live analysis is not available from this browser session; curated showcase is still usable.';
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
  list.replaceChildren();
  for (const sample of state.data.samples) {
    const button = document.createElement('button');
    button.className = 'sample-button';
    button.type = 'button';
    button.dataset.id = sample.id;
    button.appendChild(textElement('strong', sample.title));
    button.appendChild(textElement('span', sample.label.replaceAll('_', ' ')));
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
    replaceWithImage(imageHint, sample.imageSrc, sample.imageAlt || sample.imageHint, 'preview-image');
  } else {
    imageHint.textContent = sample.imageHint;
  }
}

function renderFrontier() {
  const grid = $('#frontier-grid');
  grid.replaceChildren();
  for (const profile of state.data.frontier) {
    const card = document.createElement('article');
    card.className = 'frontier-card';
    const speedWidth = Math.max(8, Math.min(100, 100 - (profile.latencyMs / 4000) * 100));
    appendText(card, 'span', `${profile.status.toUpperCase()} · ${profile.samples} samples`, 'card-kicker');
    appendText(card, 'h3', profile.profile);
    appendText(card, 'span', fmtF1(profile.f1), 'big-number');
    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.setAttribute('aria-label', 'Latency headroom under 4 second budget');
    const fill = document.createElement('span');
    fill.style.width = `${speedWidth}%`;
    bar.appendChild(fill);
    card.appendChild(bar);
    appendText(card, 'p', profile.useCase, 'muted');
    const latency = document.createElement('p');
    appendText(latency, 'span', 'Latency:', 'decision');
    latency.append(` ${fmtLatency(profile.latencyMs)}`);
    card.appendChild(latency);
    appendText(card, 'p', `Run: ${profile.run}`, 'muted small');
    grid.appendChild(card);
  }

  const context = document.createElement('article');
  context.className = 'frontier-card';
  appendText(context, 'span', 'FIELD BUDGET', 'card-kicker');
  appendText(context, 'h3', '4,000 ms ceiling');
  appendText(context, 'span', '< 0.3s', 'big-number');
  appendText(context, 'p', 'Both public profiles stay far below the mission-critical limit, preserving time for human decision-making.', 'muted');
  const strategy = document.createElement('p');
  appendText(strategy, 'span', 'Strategy:', 'decision');
  strategy.append(' choose speed for volume; choose accuracy for critical review.');
  context.appendChild(strategy);
  grid.appendChild(context);
}

function renderExperiments() {
  const board = $('#experiment-board');
  board.replaceChildren();
  for (const experiment of state.data.experiments) {
    const card = document.createElement('article');
    card.className = 'experiment-card';
    const isWinner = experiment.id.includes('480');
    appendText(card, 'span', experiment.id, 'card-kicker');
    appendText(card, 'h3', experiment.label);
    appendText(card, 'p', `Technical note: ${experiment.technicalLabel || experiment.id}`, 'muted small');
    const metrics = document.createElement('p');
    appendText(metrics, 'span', 'F1:', 'decision');
    metrics.append(` ${fmtF1(experiment.f1)} · `);
    appendText(metrics, 'span', 'Latency:', 'decision');
    metrics.append(` ${fmtLatency(experiment.latencyMs)}`);
    card.appendChild(metrics);
    const decision = appendText(card, 'p', experiment.decision, 'decision');
    decision.style.color = isWinner ? 'var(--green)' : 'var(--warning)';
    const changed = document.createElement('p');
    appendText(changed, 'span', 'What changed:', 'decision');
    changed.append(` ${experiment.change || experiment.label}`);
    card.appendChild(changed);
    appendText(card, 'p', experiment.detail, 'muted');
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
  const sendButton = $('#send-coordinator');
  const copyRadioButton = $('#copy-radio-script');
  const copyHandoffButton = $('#copy-handoff-summary');
  const exportReviewPacketButton = $('#export-review-packet');
  const exportQueueButton = $('#export-incident-queue');
  if (!form || !reportInput) return;

  const bridgeSample = state.data?.samples?.find((sample) => sample.id === 'bridge-flood') || state.data?.samples?.[0];
  let latestIncident = null;
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
  const clearBridgeDefaultsForNewInput = () => {
    reportInput.value = '';
    $('#phone-report-title').textContent = 'New field report';
    $('#phone-report-note').textContent = 'New media selected. Add a short note, then run Edge-Triage.';
    $('#phone-priority').textContent = 'Awaiting analysis';
    $('#app-result-title').textContent = 'No triage result yet';
    $('#app-result-summary').textContent = 'New input selected. Run Edge-Triage to create a fresh triage card.';
    $('#app-result-label').textContent = 'Awaiting analysis';
    $('#app-result-priority').textContent = 'Awaiting analysis';
    $('#app-result-latency').textContent = 'Awaiting run';
    $('#app-result-action').textContent = 'No safe next action is generated until the volunteer runs Edge-Triage.';
    renderActionPack(null);
    renderRedFlags([]);
    renderGuidanceBasis([]);
    $('#app-radio-script').textContent = 'Run triage to generate a short handoff script.';
    $('#app-handoff').textContent = 'Ready for coordinator handoff after review. Human review required before operational decisions.';
    status.textContent = 'New media selected. Add a short field note, then run Edge-Triage.';
    status.classList.remove('complete', 'error');
  };
  const updateImagePreview = () => {
    const file = imageInput?.files?.[0];
    const preview = $('#field-image-preview');
    const phonePreview = $('#phone-image-preview');
    if (!file || !preview || !phonePreview) return;
    const reader = new FileReader();
    reader.onload = () => {
      const imageSrc = reader.result;
      preview.src = imageSrc;
      preview.classList.remove('hidden');
      phonePreview.classList.remove('empty');
      replaceWithImage(phonePreview, imageSrc, 'Selected field report preview');
    };
    reader.readAsDataURL(file);
  };
  const formatActionPack = (pack) => {
    if (!pack) return 'Responder checklist unavailable for this result.';
    const collect = (pack.collectNext || pack.collect_next || []).join(', ');
    const escalate = (pack.escalateIf || pack.escalate_if || []).join(', ');
    const doNot = pack.doNotDo || pack.do_not_do || 'Do not self-deploy into active hazards.';
    return `Do not do: ${doNot} Collect next: ${collect}. Escalate if: ${escalate}.`;
  };
  const renderList = (target, items, fallback) => {
    const list = $(target);
    if (!list) return;
    const values = (items || []).filter(Boolean);
    list.replaceChildren(...(values.length ? values : [fallback]).map((item) => textElement('li', item)));
  };
  const renderActionPack = (pack) => {
    const collect = (pack?.collectNext || pack?.collect_next || []).join(', ');
    const escalate = (pack?.escalateIf || pack?.escalate_if || []).join(', ');
    const doNot = pack?.doNotDo || pack?.do_not_do || 'Do not self-deploy into active hazards.';
    const routeTo = pack?.routeTo || pack?.route_to || 'human coordinator review';
    const items = [
      `Do not do: ${doNot}`,
      collect ? `Collect next: ${collect}` : '',
      escalate ? `Escalate if: ${escalate}` : '',
      `Route to: ${routeTo}`
    ];
    renderList('#app-action-pack-list', items, 'Responder checklist unavailable for this result.');
    $('#app-action-pack').textContent = formatActionPack(pack);
  };
  const renderRedFlags = (redFlags) => {
    const card = $('#app-red-flag-card');
    const flags = (redFlags || []).map((flag) => flag.description || flag.pattern || String(flag));
    if (card) card.hidden = flags.length === 0;
    renderList('#app-red-flags', flags, 'No red flags detected.');
  };
  const renderGuidanceBasis = (guidance) => {
    renderList('#app-guidance-basis', guidance, 'Conservative guidance basis unavailable for this result.');
  };
  const buildHandoffSummary = (record) => {
    if (!record) return 'No reviewed triage card is ready yet.';
    const action = record.nextAction || record.next_action || 'Safe next action unavailable.';
    return [
      `Report: ${record.report || 'No field report supplied.'}`,
      `Label: ${record.label || 'unknown'}`,
      `Priority: ${record.priority || 'unknown'}`,
      `Safe next action: ${action}`,
      'Boundary: Decision support only; human review required before coordinator action.'
    ].join('\n');
  };
  const copyText = async (text, successMessage) => {
    if (!text || text.includes('unavailable') || text.includes('No reviewed triage card')) {
      setVolunteerError('Run Edge-Triage before copying a handoff artifact.');
      return;
    }
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const fallback = document.createElement('textarea');
        fallback.value = text;
        fallback.setAttribute('readonly', '');
        fallback.style.position = 'fixed';
        fallback.style.left = '-9999px';
        document.body.appendChild(fallback);
        fallback.select();
        document.execCommand('copy');
        fallback.remove();
      }
      status.textContent = successMessage;
      status.classList.add('complete');
      status.classList.remove('error');
    } catch (error) {
      console.error(error);
      setVolunteerError('Copy failed in this browser. You can still read the text on screen.');
    }
  };
  const exportReviewPacket = () => {
    if (!latestIncident) {
      setVolunteerError('Run Edge-Triage before exporting a review packet.');
      return;
    }
    const packet = {
      ...latestIncident,
      handoffSummary: buildHandoffSummary(latestIncident),
      reviewChecklist: [
        'Confirm location, time, source, affected people, and visible hazards through normal coordinator channels.',
        'Review red flags and safe next action before assigning volunteer movement.',
        'Treat this as a local handoff aid only; no automatic sync, dispatch, diagnosis, or incident-command authority.'
      ]
    };
    const link = document.createElement('a');
    link.href = `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(packet, null, 2))}`;
    link.download = 'edge-triage-review-packet.json';
    link.click();
    status.textContent = 'Exported single review packet. No network sync, dispatch, or acknowledgement was performed.';
    status.classList.add('complete');
    status.classList.remove('error');
  };
  const saveIncident = (record) => {
    const key = 'edge-triage-incident-queue';
    const queue = JSON.parse(localStorage.getItem(key) || '[]');
    const incident = { ...record, savedAt: new Date().toISOString(), synced: false };
    queue.push(incident);
    latestIncident = incident;
    localStorage.setItem(key, JSON.stringify(queue));
    $('#handoff-status').textContent = `${queue.length} local incident${queue.length === 1 ? '' : 's'} queued`;
    return queue.length;
  };
  const exportIncidentQueue = () => {
    const queue = localStorage.getItem('edge-triage-incident-queue') || '[]';
    const link = document.createElement('a');
    link.href = `data:application/json;charset=utf-8,${encodeURIComponent(queue)}`;
    link.download = 'edge-triage-incident-queue.json';
    link.click();
    status.textContent = 'Exported local incident queue. No network sync was performed.';
    status.classList.add('complete');
    status.classList.remove('error');
  };
  const renderFieldResult = (sample, report) => {
    const title = report.split(/[.!?]/).find(Boolean)?.trim() || sample.title || 'Field report';
    $('#app-result-title').textContent = title;
    $('#app-result-summary').textContent = `This report looks like ${sample.title.toLowerCase()}. Edge-Triage converted the field note into a triage card that can be reviewed before coordinator handoff.`;
    $('#app-result-label').textContent = sample.label;
    $('#app-result-priority').textContent = sample.priority;
    $('#app-result-latency').textContent = fmtLatency(sample.latencyMs);
    $('#app-result-action').textContent = sample.nextAction;
    renderActionPack(sample.actionPack);
    renderRedFlags(sample.redFlags || []);
    renderGuidanceBasis(sample.guidanceBasis || []);
    $('#app-radio-script').textContent = sample.radioScript || 'Radio script unavailable for this curated scenario.';
    const queued = saveIncident({ report, label: sample.label, priority: sample.priority, nextAction: sample.nextAction, source: 'curated-demo', actionPack: sample.actionPack, radioScript: sample.radioScript, guidanceBasis: sample.guidanceBasis, redFlags: sample.redFlags || [] });
    $('#app-handoff').textContent = `Saved locally as incident ${queued}. Ready for coordinator handoff after review. Human review required before operational decisions.`;
    $('#phone-report-title').textContent = title;
    $('#phone-report-note').textContent = report;
    $('#phone-priority').textContent = sample.priority;
    status.textContent = `Triage card updated: ${sample.priority}. Review the safe next action, then send to coordinator if appropriate.`;
    status.classList.add('complete');
    status.classList.remove('error');
  };
  const renderVolunteerLiveResult = (result, report, fileName) => {
    const title = report.split(/[.!?]/).find(Boolean)?.trim() || `Live upload: ${fileName}`;
    $('#app-result-title').textContent = title;
    $('#app-result-summary').textContent = `${result.scene_summary || 'Live Gemma returned a triage result for the selected image.'} ${result.disclaimer || 'Decision support only.'}`;
    $('#app-result-label').textContent = result.label;
    $('#app-result-priority').textContent = result.priority;
    $('#app-result-latency').textContent = fmtLatency(Number(result.latency_ms || 0));
    $('#app-result-action').textContent = result.next_action;
    renderActionPack(result.action_pack);
    renderRedFlags(result.red_flags || []);
    renderGuidanceBasis(result.guidance_basis || []);
    $('#app-radio-script').textContent = result.radio_script || 'Radio script unavailable for this result.';
    const queued = saveIncident({ report, label: result.label, priority: result.priority, nextAction: result.next_action, source: result.live_model ? 'live-gemma' : 'guarded-fallback', actionPack: result.action_pack, radioScript: result.radio_script, redFlags: result.red_flags || [], guidanceBasis: result.guidance_basis || [] });
    $('#app-handoff').textContent = `Saved locally as incident ${queued}. Ready for coordinator handoff after review. Human review required before operational decisions.`;
    $('#phone-report-title').textContent = title;
    $('#phone-report-note').textContent = report || `Image selected: ${fileName}`;
    $('#phone-priority').textContent = result.priority;
    status.textContent = `${result.live_model ? 'Live Gemma analysis complete' : 'Guarded API analysis complete'}: ${result.priority}. Review before coordinator handoff.`;
    status.classList.add('complete');
    status.classList.remove('error');
  };
  const setVolunteerError = (message) => {
    status.textContent = message;
    status.classList.add('error');
    status.classList.remove('complete');
  };
  const runVolunteerLiveInference = async (report) => {
    const file = imageInput?.files?.[0];
    if (!file) {
      setVolunteerError('Real analysis needs an image. Add a photo, then run Edge-Triage.');
      imageInput?.focus();
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setVolunteerError('Image must be 25 MB or smaller.');
      return;
    }
    const formData = new FormData();
    formData.append('image', file);
    formData.append('note', report);
    status.textContent = 'Running real Live Gemma analysis…';
    status.classList.remove('complete', 'error');
    try {
      const response = await fetch('/api/triage', {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        setVolunteerError(await friendlyLiveError(response));
        return;
      }
      const result = await response.json();
      renderVolunteerLiveResult(result, report, file.name);
    } catch (error) {
      console.error(error);
      setVolunteerError('Live Gemma analysis is unavailable right now. No static bridge result was generated.');
    }
  };

  reportInput.addEventListener('input', saveDraft);
  imageInput?.addEventListener('change', () => {
    updateFileName(imageInput, $('#field-image-name'), 'No image selected');
    updateImagePreview();
    clearBridgeDefaultsForNewInput();
    saveDraft();
  });
  audioInput?.addEventListener('change', () => {
    updateFileName(audioInput, $('#field-audio-name'), 'No audio selected');
    clearBridgeDefaultsForNewInput();
    saveDraft();
  });
  bridgeButton?.addEventListener('click', () => {
    reportInput.value = 'Bridge washed out after flood. Road blocked. No injuries visible. Need routing guidance.';
    saveDraft();
    renderFieldResult(bridgeSample, reportInput.value);
  });
  sendButton?.addEventListener('click', () => {
    if (!latestIncident) {
      setVolunteerError('Run Edge-Triage before marking a report ready for coordinator review.');
      return;
    }
    $('#app-handoff').textContent = buildHandoffSummary(latestIncident);
    status.textContent = 'Marked ready for coordinator review. This prototype keeps the handoff local for the judge demo.';
    status.classList.add('complete');
    status.classList.remove('error');
    $('#handoff-status').textContent = 'Ready for coordinator review';
  });
  copyRadioButton?.addEventListener('click', () => copyText(latestIncident?.radioScript || $('#app-radio-script').textContent, 'Copied radio script for human-reviewed handoff.'));
  copyHandoffButton?.addEventListener('click', () => copyText(buildHandoffSummary(latestIncident), 'Copied coordinator handoff summary.'));
  exportReviewPacketButton?.addEventListener('click', exportReviewPacket);
  exportQueueButton?.addEventListener('click', exportIncidentQueue);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const report = reportInput.value.trim();
    saveDraft();
    runVolunteerLiveInference(report);
  });
  saveDraft();
}

loadData().catch((error) => {
  console.error(error);
  const banner = document.createElement('div');
  banner.className = 'app-error-banner';
  banner.textContent = error.message || 'Could not load Edge-Triage demo.';
  document.body.prepend(banner);
});
