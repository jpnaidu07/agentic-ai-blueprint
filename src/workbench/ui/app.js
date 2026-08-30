'use strict';

const $ = id => document.getElementById(id);
const state = {csrf: '', sessionToken: '', connected: false, provider: '', model: '', solutions: [], selected: null, detail: null, catalog: [], activeRun: null, view: 'home', timer: null};
const labels = {home: 'Overview', setup: 'Setup & models', solutions: 'Solutions', library: 'Specs & skills', runs: 'Run history', apps: 'Applications'};

function element(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = String(text);
  if (className) result.className = className;
  return result;
}
function button(text, callback, className = 'secondary') {
  const result = element('button', text, className);
  result.type = 'button';
  result.addEventListener('click', event => perform(result, () => callback(event)));
  return result;
}
function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').hidden = !message;
  $('notice').classList.toggle('error', error);
}
async function perform(control, callback) {
  if (control.disabled) return;
  control.disabled = true;
  try { await callback(); } catch (error) { notice(error.message || 'Operation failed.', true); }
  finally { control.disabled = false; }
}
function click(id, callback) { $(id).addEventListener('click', () => perform($(id), callback)); }
function submit(id, callback) {
  $(id).addEventListener('submit', event => {
    event.preventDefault();
    const control = event.submitter || $(id).querySelector('button');
    perform(control, callback);
  });
}
async function api(path, options = {}) {
  const headers = {'X-Workbench-CSRF': state.csrf, ...(state.sessionToken ? {Authorization: `Bearer ${state.sessionToken}`} : {}), ...options.headers};
  let body = options.body;
  if (body !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(body); }
  const response = await fetch(path, {...options, body, headers, credentials: 'omit'});
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== '/api/session') lock();
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed. Check required fields.');
  }
  return data;
}
function syncConnection(data) {
  state.connected = Boolean(data.connected);
  state.provider = data.provider || '';
  state.model = data.model || '';
  $('provider-status').textContent = state.connected ? `${state.provider} / ${state.model}` : 'No model connected';
  $('stat-model').textContent = state.connected ? state.provider : 'Not set';
  $('provider-status').classList.toggle('green', state.connected);
  $('connection-dot').classList.toggle('connected', state.connected);
}
function lock() {
  clearTimeout(state.timer);
  state.csrf = '';
  state.sessionToken = '';
  $('workspace').hidden = true;
  $('pairing').hidden = false;
  $('disconnect-session').hidden = true;
  $('api-key').value = '';
  $('role-tokens').replaceChildren();
  syncConnection({connected: false});
}
async function unlock(data) {
  state.csrf = data.csrf;
  state.sessionToken = data.session_token || state.sessionToken;
  syncConnection(data);
  $('pairing').hidden = true;
  $('workspace').hidden = false;
  $('disconnect-session').hidden = false;
  await Promise.all([loadSolutions(), loadCatalog()]);
}
async function show(view) {
  state.view = view;
  Object.keys(labels).forEach(key => $(`view-${key}`).hidden = key !== view);
  document.querySelectorAll('nav [data-view]').forEach(control => {
    control.classList.toggle('active', control.dataset.view === view);
    if (control.dataset.view === view) control.setAttribute('aria-current', 'page');
    else control.removeAttribute('aria-current');
  });
  $('page-name').textContent = labels[view];
  document.title = `${labels[view]} · Blueprint Workbench`;
  if (view !== 'apps') { $('role-tokens').replaceChildren(); $('role-tokens').hidden = true; }
  if (!state.csrf) return;
  if (view === 'solutions') await loadSolutions();
  if (view === 'runs') await loadRuns();
  if (view === 'apps') await loadApps();
  $('main').focus({preventScroll: true});
}
document.querySelectorAll('[data-view]').forEach(control => control.addEventListener('click', () => perform(control, () => show(control.dataset.view))));
submit('pair-form', async () => {
  const token = $('pair-token').value;
  $('pair-token').value = '';
  const data = await api('/api/session', {method: 'POST', headers: {Authorization: `Bearer ${token}`}});
  await unlock(data);
  notice('Browser paired. Explore the reference, or connect a model to begin a new solution.');
});
click('disconnect-session', async () => { await api('/api/session', {method: 'DELETE'}); lock(); notice('Workspace locked.'); });
click('home-new', async () => { await show('solutions'); $('brief-form').hidden = false; $('solution-name').focus(); });
click('new-solution', () => { $('brief-form').hidden = !$('brief-form').hidden; if (!$('brief-form').hidden) $('solution-name').focus(); });
click('home-tender', async () => { await show('solutions'); await selectSolution('government-tender-processing'); });
click('refresh-home', async () => { await Promise.all([loadSolutions(), loadCatalog()]); notice('Workspace refreshed.'); });

const providerDocs = {openai: 'https://developers.openai.com/api/docs/models', gemini: 'https://ai.google.dev/gemini-api/docs/openai', ollama: 'https://docs.ollama.com/openai'};
$('provider').addEventListener('change', () => {
  $('key-label').hidden = $('provider').value === 'ollama';
  $('api-key').value = '';
  $('model').value = '';
  $('model-list').replaceChildren();
  $('provider-docs').href = providerDocs[$('provider').value];
  $('context-window').value = $('provider').value === 'ollama' ? '16384' : '65536';
  $('max-tokens').value = $('provider').value === 'ollama' ? '4096' : '8192';
});
click('list-models', async () => {
  const data = await api('/api/providers/models', {method: 'POST', body: {provider: $('provider').value, api_key: $('api-key').value}});
  $('model-list').replaceChildren(...data.models.map(name => { const option = element('option'); option.value = name; return option; }));
  notice(`${data.models.length} models listed. ${data.note}`);
  $('model').focus();
});
submit('connection-form', async () => {
  const body = {provider: $('provider').value, model: $('model').value, api_key: $('api-key').value, max_tokens: Number($('max-tokens').value), context_window: Number($('context-window').value), consent: $('provider-consent').checked};
  try {
    const data = await api('/api/connection', {method: 'POST', body});
    syncConnection({connected: true, provider: data.provider, model: data.model});
    $('connection-result').textContent = `Structured output verified · ${data.latency_ms} ms\n${data.quality_benchmark}\nUsage: ${JSON.stringify(data.usage)}`;
    $('connection-result').hidden = false;
    notice('Model connected. You can now generate capabilities or ask for advice.');
  } finally { $('api-key').value = ''; body.api_key = ''; }
});
click('disconnect-model', async () => {
  await api('/api/connection', {method: 'DELETE'});
  syncConnection({connected: false});
  $('api-key').value = '';
  $('connection-result').hidden = true;
  notice('Model disconnected. In-flight calls release their keys when they finish.');
});
click('scan-system', async () => {
  notice('Checking CPU, memory, local runtimes and Docker readiness…');
  const data = await api('/api/system');
  const stats = [['PROCESSOR', data.cpu, `${data.logical_cpus || '?'} logical CPUs · ${data.architecture}`], ['SYSTEM MEMORY', data.ram_gb ? `${data.ram_gb} GiB` : 'Unknown', `${data.available_ram_gb ?? '?'} GiB currently available`], ['GRAPHICS', data.gpu, 'Acceleration must be tested'], ['LOCAL TOOLS', data.tools.docker_ready ? 'Docker ready' : 'Docker needs setup', `Ollama: ${data.tools.ollama_ready ? 'running' : data.tools.ollama ? 'installed' : 'not found'} · ${data.disk_free_gb} GiB free`]];
  $('hardware').replaceChildren(...stats.map(([label, value, note]) => {
    const card = element('div'); card.append(element('span', label), element('strong', value), element('small', note)); return card;
  }));
  $('local-models').replaceChildren(...data.local_models.map(model => {
    const card = element('article', undefined, 'card');
    const head = element('div', undefined, 'section-head');
    head.append(element('h2', model.id), element('span', model.fits_estimate ? 'Fits memory estimate' : 'Outside safe estimate', `pill ${model.fits_estimate ? 'green' : 'warn'}`));
    card.append(head, element('p', model.purpose), element('p', `Download ≈ ${model.download_gb} GB · runtime budget ≈ ${model.working_gb} GiB, plus OS/services. ${model.available_now_estimate ? 'Current free memory meets the conservative estimate.' : 'Close other workloads or check available memory before running.'}`));
    const installed = data.installed_models.includes(model.id);
    card.append(button(installed ? 'Select installed model' : 'Review model download…', async () => {
      if (installed) { $('provider').value = 'ollama'; $('provider').dispatchEvent(new Event('change')); $('model').value = model.id; $('connection-form').scrollIntoView({behavior: 'smooth'}); }
      else await systemAction('pull-model', model.id);
    }));
    const source = element('a', 'Model card & current download details ↗'); source.href = model.source; source.target = '_blank'; source.rel = 'noopener noreferrer'; card.append(source);
    return card;
  }));
  notice(`Detected ${data.os}. Hardware fit is an estimate; connection and task evaluations remain separate.`);
});

async function loadCatalog() {
  const data = await api('/api/catalog');
  state.catalog = data.items;
  $('stat-skills').textContent = data.items.filter(item => item.kind === 'skill').length;
  $('module-list').replaceChildren(...data.modules.map(module => {
    const card = element('div', undefined, 'module-card'); card.append(element('span', String(module.number).padStart(2, '0')), element('strong', module.name)); return card;
  }));
  renderCatalog();
}
function renderCatalog() {
  const query = $('library-filter').value.toLowerCase();
  $('library-list').replaceChildren(...state.catalog.filter(item => `${item.name} ${item.description}`.toLowerCase().includes(query)).map(item => {
    const control = button('', async () => {
      const data = await api(`/api/catalog/content?item=${encodeURIComponent(item.id)}`);
      $('library-title').textContent = data.path;
      $('library-content').textContent = data.content;
      document.querySelectorAll('.library-item').forEach(node => node.classList.remove('active')); control.classList.add('active');
    }, 'library-item');
    control.append(element('strong', item.name), element('small', item.description)); return control;
  }));
}
$('library-filter').addEventListener('input', renderCatalog);
async function loadSolutions() {
  state.solutions = await api('/api/solutions');
  $('stat-solutions').textContent = state.solutions.length;
  $('solution-list').replaceChildren(...state.solutions.map(item => {
    const control = button('', () => selectSolution(item.name), `solution-choice${state.selected === item.name ? ' active' : ''}`);
    control.append(element('strong', item.title), element('small', `${item.name}\n${item.stage} · ${item.completed}/${item.tasks} task receipts`));
    return control;
  }));
  if (!state.solutions.length) $('solution-list').append(element('p', 'No solutions yet. Start with a problem statement.', 'subtle'));
}
submit('brief-form', async () => {
  if (!state.connected) throw new Error('Connect a model in Setup & models before generating a capability.');
  const job = await api('/api/solutions', {method: 'POST', body: {name: $('solution-name').value, problem: $('problem').value, constraints: $('solution-constraints').value}});
  state.selected = $('solution-name').value;
  await followJob(job);
});
async function selectSolution(name) {
  const data = await api(`/api/solutions/${encodeURIComponent(name)}`);
  state.selected = name; state.detail = data;
  document.querySelectorAll('.solution-choice').forEach((control, i) => control.classList.toggle('active', state.solutions[i]?.name === name));
  renderSolution(data);
}
function field(labelText, input) { const label = element('label', labelText); label.append(input); return label; }
function check(labelText, id, checked = false) {
  const label = element('label', undefined, 'check'); const input = element('input'); input.type = 'checkbox'; input.id = id; input.checked = checked;
  label.append(input, element('span', labelText)); return label;
}
function option(value, label) { const node = element('option', label); node.value = value; return node; }
function renderSolution(data) {
  const container = $('solution-detail'); container.replaceChildren();
  const heading = element('div', undefined, 'solution-header');
  const title = element('div'); title.append(element('span', data.reference ? 'INCLUDED REFERENCE' : 'SOLUTION WORKSPACE', 'eyebrow'), element('h2', data.solution));
  heading.append(title, element('span', data.approved ? 'Specs approved' : 'Review required', `pill ${data.approved ? 'green' : 'warn'}`)); container.append(heading);
  if (data.issue) container.append(element('p', data.issue, 'callout'));
  if (data.reference) container.append(element('p', 'The tender code already exists in src/tender and the shared provider/API modules. Explore it in Applications. The bounded UI writer never overwrites shared repository source.', 'callout'));
  const toolbar = element('div', undefined, 'solution-toolbar');
  for (const [stage, label] of [['design', 'Generate design'], ['decomposition', 'Generate decomposition'], ['remaining', 'Generate remaining specs']]) {
    const control = button(label, async () => {
      if (!state.connected) throw new Error('Connect a model before generating specs.');
      await followJob(await api(`/api/solutions/${data.solution}/stages`, {method: 'POST', body: {stage}}));
    });
    const hasDesign = data.files.some(file => file.path === 'design/architecture.yaml');
    const hasTasks = data.files.some(file => file.path === 'decomposition/tasks.yaml');
    control.disabled = stage === 'design' ? hasDesign : stage === 'decomposition' ? hasTasks || !hasDesign : hasDesign && hasTasks;
    if (control.disabled) control.title = 'Existing specifications are preserved. Review or edit their YAML below.';
    toolbar.append(control);
  }
  toolbar.append(button('Refresh status', () => selectSolution(data.solution), 'quiet'));
  container.append(toolbar);
  const picker = element('select'); picker.id = 'artifact-picker';
  picker.append(...data.files.map(file => option(file.path, file.path)));
  const editor = element('textarea', undefined, 'artifact-editor'); editor.id = 'artifact-editor'; editor.setAttribute('aria-label', 'Specification artifact content'); editor.spellcheck = false;
  const save = button('Save reviewed YAML', async () => {
    const file = data.files.find(value => value.path === picker.value);
    const section = picker.value.split('/')[0];
    if (!file || !picker.value.endsWith('.yaml')) throw new Error('Select a structured YAML file to edit. Markdown views are generated from it.');
    if (!await confirmation('Save specification changes?', 'This changes the reviewed specification, updates its paired Markdown and may invalidate downstream specs and approval. A local backup is retained.', picker.value)) return;
    const result = await api(`/api/solutions/${data.solution}/specs`, {method: 'PUT', body: {section, content: editor.value, sha256: file.sha256, confirmed: true}});
    notice(result.message); await selectSolution(data.solution);
  }, 'secondary small');
  function selectArtifact() { const file = data.files.find(value => value.path === picker.value); editor.value = file?.content || ''; editor.readOnly = !['capability/capability.yaml','design/architecture.yaml','decomposition/tasks.yaml'].includes(picker.value); save.hidden = editor.readOnly; }
  picker.addEventListener('change', selectArtifact); selectArtifact();
  container.append(field('Review an actual specification file', picker), editor, save);
  if (data.spec_digest) {
    const approval = element('div', undefined, 'run-controls');
    const reviewer = element('input'); reviewer.placeholder = 'Your name'; reviewer.id = 'reviewer-name'; reviewer.maxLength = 80;
    approval.append(element('h3', 'Approve this specification version'), field('Reviewer identity', reviewer), check('I reviewed capability, design, decomposition and unresolved questions. I approve local engineering against this exact version.', 'approve-check'));
    approval.append(button('Approve current specs', async () => {
      const result = await api(`/api/solutions/${data.solution}/approve`, {method: 'POST', body: {reviewer: reviewer.value, confirmed: $('approve-check').checked, spec_digest: data.spec_digest}});
      notice(result.message); await selectSolution(data.solution);
    }, 'primary')); container.append(approval);
  }
  if (data.tasks.length) {
    const controls = element('div', undefined, 'run-controls');
    controls.append(element('h3', 'Choose how you want to work'), element('p', data.reference ? 'Prepare a step-by-step teaching plan for the existing reference. Use a coding agent/developer to extend its shared source; this action makes no LLM calls and runs no code.' : 'Generate selected source, or also test it inside Docker. A task is not complete merely because files were created.', 'subtle'));
    const selector = element('select'); selector.id = 'run-selector';
    selector.append(...[['next','Next ready task'],['all','All tasks (bounded run)'],...['database','backend','agents','rag','frontend','security','infrastructure','tests','evals','deployment'].map(skill => [skill,skill]),...data.tasks.map(task => [task.id,task.id])].map(([value,label]) => option(value,label)));
    const module = element('select'); module.id = 'run-module'; module.append(option('','Use task/skill scope'), ...Array.from({length:8},(_,i)=>option(String(i+1),`Blueprint section ${i+1}`)));
    const grid = element('div', undefined, 'form-grid'); grid.append(field('Task scope', selector), field('Or numbered blueprint section', module)); controls.append(grid);
    controls.append(check('Include unfinished prerequisites outside this selection.', 'include-dependencies'));
    if (!data.reference) controls.append(check('Also execute generated acceptance tests in the isolated Docker runner. This requires Docker and the runner image.', 'execute-tests'));
    controls.append(check(data.reference ? 'I authorize creating the selected teaching plan inside this solution. This does not execute the plan or send data to a model.' : 'I authorize this selected run, writes only inside this solution runtime, and sending the selected specs/code to the connected model.', 'run-confirmed'));
    controls.append(button(data.reference ? 'Prepare reference teaching plan' : 'Run selected engineering steps →', async () => {
      const body = {selector: module.value ? 'next' : selector.value, module: module.value ? Number(module.value) : null, include_dependencies: $('include-dependencies').checked, execute: $('execute-tests')?.checked || false, confirmed: $('run-confirmed').checked, max_tasks: 12};
      await followJob(await api(`/api/solutions/${data.solution}/run`, {method:'POST', body}));
    }, 'primary'));
    if (!data.reference) controls.append(button('Launch verified preview', () => systemAction('launch-generated', undefined, data.solution), 'quiet'));
    container.append(controls, element('h3','Dependency-aware task progress'));
    const scroll = element('div', undefined, 'table-scroll'), table = element('table', undefined, 'task-table'), head = element('tr');
    ['Task / objective','Skill / sections','State'].forEach(label => head.append(element('th', label))); const thead=element('thead'); thead.append(head); table.append(thead);
    const tbody=element('tbody'); data.tasks.forEach(task => {
      const row=element('tr'), description=element('td'), skill=element('td'), status=element('td');
      description.append(element('strong',task.id),element('small',task.objective)); if(task.dependencies.length) description.append(element('small',`Needs: ${task.dependencies.join(', ')}`));
      skill.append(element('span',task.skill),element('small',`Sections ${task.modules.join(', ')}`)); status.append(element('span',task.state,`pill ${task.state==='complete'?'green':task.ready?'':'warn'}`)); row.append(description,skill,status); tbody.append(row);
    }); table.append(tbody); scroll.append(table); container.append(scroll);
  }
}

submit('ask-form', async () => {
  if (!state.connected) throw new Error('Connect a model before asking for advice.');
  const job = await api('/api/ask', {method: 'POST', body: {text: $('ask-text').value, solution: state.selected}});
  await followJob(job);
});
async function followJob(job) {
  state.activeRun = job.id; await show('runs'); renderRun(job); await watch(job.id);
}
async function watch(id) {
  clearTimeout(state.timer);
  if (!state.csrf) return;
  try {
    const job = await api(`/api/jobs/${id}`);
    if (state.activeRun === id) renderRun(job);
    if (job.state === 'running') { state.timer = setTimeout(() => watch(id), 1500); return; }
    await Promise.all([loadRuns(),loadSolutions()]);
    notice(job.state === 'succeeded' ? 'Operation finished. Review its results and remaining task gates.' : (job.result.message || `Operation ${job.state}.`),job.state !== 'succeeded');
    if (job.kind === 'advice' && job.result.answer) { $('advice-answer').textContent=[job.result.answer,...job.result.next_steps.map(step=>`• ${step}`),...job.result.limitations.map(step=>`Limit: ${step}`)].join('\n\n'); $('advice-answer').hidden=false; }
    if (job.result.url && state.view === 'runs') await show('apps');
  } catch(error) { notice(error.message,true); }
}
async function loadRuns() {
  const runs = await api('/api/jobs');
  $('run-list').replaceChildren(...runs.map(job => {
    const control=button('',async()=>{state.activeRun=job.id;renderRun(await api(`/api/jobs/${job.id}`));if(job.state==='running')await watch(job.id);},`run-choice${state.activeRun===job.id?' active':''}`);
    control.append(element('strong',`${job.kind} · ${job.state}`),element('small',`${job.solution || 'Workspace advice'}\n${new Date(job.created).toLocaleString()}`));return control;
  }));
  if (!runs.length) $('run-list').append(element('p','No runs yet. Connect a model and create a solution, or launch the reference app.','subtle'));
}
click('refresh-runs', loadRuns);
function renderRun(job) {
  const view=$('run-detail');view.replaceChildren();
  const heading=element('div',undefined,'section-head');heading.append(element('h2',`${job.kind} / ${job.solution || 'workspace'}`),element('span',job.state,`pill ${job.state==='succeeded'?'green':job.state==='running'?'':'warn'}`));view.append(heading);
  view.append(element('p',`Run ${job.id.slice(0,8)} · ${new Date(job.created).toLocaleString()}`,'subtle'));
  if(job.state==='running')view.append(button('Cancel at next safe boundary',async()=>{const result=await api(`/api/jobs/${job.id}/cancel`,{method:'POST'});notice(result.message);},'quiet small'));
  for(const event of job.events){const row=element('div',undefined,`event ${event.level==='warning'?'warning':''}`);row.append(element('small',new Date(event.at).toLocaleTimeString()),element('div',event.message));view.append(row);}
  if(!job.events.length && job.state==='running')view.append(element('p','Operation queued; progress will appear here.','subtle'));
  if(job.state!=='running'){
    const result=element('div',undefined,'run-result');result.append(element('h3','Result & next actions'));
    if(job.result.message)result.append(element('p',job.result.message));
    if(job.result.answer)result.append(element('p',job.result.answer,'prose'));
    result.append(element('pre',JSON.stringify(job.result,null,2),'file-view'));view.append(result);
    if(job.solution)view.append(button('Back to solution',async()=>{await show('solutions');await selectSolution(job.solution);},'secondary small'));
  }
}

async function confirmation(title, description, command) {
  const dialog=$('action-dialog');$('action-title').textContent=title;$('action-description').textContent=description;$('action-command').textContent=command;
  $('action-confirmed').checked=false;$('action-proceed').disabled=true;dialog.returnValue='cancel';dialog.showModal();
  return new Promise(resolve=>dialog.addEventListener('close',()=>resolve(dialog.returnValue==='default' && $('action-confirmed').checked),{once:true}));
}
$('action-confirmed').addEventListener('change',()=>{$('action-proceed').disabled=!$('action-confirmed').checked;});
async function systemAction(action, model='qwen3:4b', solution='government-tender-processing') {
  const details={
    'install-ollama':['Install Ollama?', 'The fixed installer uses Winget or Homebrew when present. It downloads software and accepts package/source terms. You may need to complete OS prompts manually.','winget install --id Ollama.Ollama --exact …\nmacOS alternative: brew install ollama'],
    'start-ollama':['Start local Ollama?', 'Starts the installed Ollama binary bound to 127.0.0.1:11434. An already running server is reused.','ollama serve (loopback only)'],
    'pull-model':['Download local model?', 'This may download several gigabytes. Hardware/disk estimates are checked; actual inference quality and GPU acceleration are not guaranteed.',`Download allowlisted model: ${model}`],
    'build-runner':['Build the isolated runner?', 'Downloads the base image and pinned Python packages using Docker. Later generated-code tests run without network or credentials.','docker build -f infra/Dockerfile.runner -t agent-blueprint-runner:local .'],
    'launch-tender':['Launch the tender reference?', 'Starts the trusted repository application on a free loopback port, creates separate local role tokens and uses persistent local SQLite. Session LLM keys are not transferred.','Trusted Python server · localhost only · synthetic data'],
    'launch-generated':['Launch verified generated code?', 'Only the current tested source/spec version can launch. It runs in a restricted container on an internal Docker network, without provider keys. Preview data is temporary.',`Solution: ${solution}\nFixed entrypoint: uvicorn app:app`],
    'stop-app':['Stop this managed application?', 'Stops only the application started by this workbench. Generated preview data in temporary storage is lost.',`Solution: ${solution}`]
  };
  const [title,description,command]=details[action];
  if(!await confirmation(title,description,command))return;
  await followJob(await api('/api/actions',{method:'POST',body:{action,model,solution,confirmed:true}}));
}
document.querySelectorAll('[data-system-action]').forEach(control=>control.addEventListener('click',()=>perform(control,()=>systemAction(control.dataset.systemAction))));
click('launch-tender',()=>systemAction('launch-tender'));
async function loadApps(){
  const apps=await api('/api/apps');
  $('app-list').replaceChildren(...apps.map(app=>{
    const card=element('article',undefined,'card');card.append(element('span',app.running?'RUNNING LOCALLY':'STOPPED','eyebrow'),element('h2',app.solution));
    const url=new URL(app.url);
    if(url.protocol==='http:' && url.hostname==='127.0.0.1' && /^\d+$/.test(url.port)) {const link=element('a',`Open application ↗ ${app.url}`,'app-url');link.href=app.url;link.target='_blank';link.rel='noopener noreferrer';card.append(link);}
    if(app.solution==='government-tender-processing')card.append(button('Reveal local role tokens',async()=>{
      const data=await api(`/api/apps/${app.solution}/credentials`,{method:'POST'});const target=$('role-tokens');target.replaceChildren(element('h2','Local development sign-in'),element('p',data.warning));
      for(const [role,token]of Object.entries(data.tokens)){const input=element('input');input.type='password';input.readOnly=true;input.value=token;input.setAttribute('aria-label',`${role} development token`);const row=element('div',undefined,'inline');row.append(input,button('Copy',async()=>{await navigator.clipboard.writeText(token);notice(`Copied ${role} token. Paste it in the tender portal sign-in.`);},'secondary small'));target.append(element('label',role),row);}
      target.append(button('Hide tokens',()=>{target.replaceChildren();target.hidden=true;},'quiet'));target.hidden=false;
    },'secondary'));
    card.append(button('Stop app',()=>systemAction('stop-app',undefined,app.solution),'quiet small'));return card;
  }));
  if(!apps.length)$('app-list').append(element('p','No managed apps are running. Launch the reference above, or launch a verified solution from its workspace.','subtle'));
}

(async()=>{try{await unlock(await api('/api/session'));}catch{lock();}})();
