let activeProblem = 'P1';
let activeMode = 'improved';

const problemsMeta = {
  P1: {
    title: '💽 OME Disk Health & SMART Triage',
    prompt: 'Perform an automated disk health triage for server SV-10492. Query Redfish storage telemetry, check Dell PowerEdge runbooks via RAG, and dispatch an idempotent service ticket if predictive failure thresholds are exceeded.',
    targetId: 'SV-10492'
  },
  P2: {
    title: '🛡️ Server Fleet Patch Automation',
    prompt: 'Generate a zero-downtime firmware upgrade and patch plan for server cluster CL-PROD-01. Build a topological dependency graph, generate a 10% canary staged rollout, verify VM evacuation pre-flight health gates, and synthesize an automated rollback manifest.',
    targetId: 'CL-PROD-01'
  },
  P3: {
    title: '🔍 Distributed Log Triage & RCA',
    prompt: 'Perform root cause analysis on distributed incident INC-LOG-992. Correlate multi-service log timestamps across OME Core, Kafka, and PostgreSQL. Search ChromaDB for matching historical post-mortems, calculate confidence score, and formulate an actionable config fix.',
    targetId: 'INC-LOG-992'
  }
};

function selectProblem(problemId) {
  activeProblem = problemId;
  document.querySelectorAll('.problem-card').forEach(c => c.classList.remove('active'));
  const el = document.getElementById(`card-${problemId}`);
  if (el) el.classList.add('active');
}

function setMode(mode) {
  activeMode = mode;
  document.getElementById('btn-mode-bf').classList.toggle('active', mode === 'brute_force');
  document.getElementById('btn-mode-imp').classList.toggle('active', mode === 'improved');
}

async function runSelectedProblem() {
  const feed = document.getElementById('trace-feed');
  feed.innerHTML = '';
  
  const statusBadge = document.getElementById('run-status');
  statusBadge.textContent = 'EXECUTING...';
  statusBadge.style.color = '#00f0ff';

  const prob = problemsMeta[activeProblem];

  if (activeMode === 'improved') {
    // Connect to SSE stream for live real-time ReAct trace
    const url = `/api/agent/stream?prompt=${encodeURIComponent(prob.prompt)}&task_id=TASK-${activeProblem}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const item = JSON.parse(event.data);
        renderTraceItem(item);
      } catch (e) {
        console.error('SSE JSON error', e);
      }
    };

    eventSource.onerror = (err) => {
      eventSource.close();
      statusBadge.textContent = 'COMPLETED';
      statusBadge.style.color = '#10b981';
      fetchFleetTelemetry();
    };
  } else {
    // Brute force synchronous call
    try {
      const resp = await fetch('/api/problems/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_id: activeProblem, mode: 'brute_force', target_id: prob.targetId })
      });
      const data = await resp.json();
      
      feed.innerHTML = `
        <div class="trace-item trace-action">
          <div class="trace-badge" style="color: #f59e0b;">STAGE 1: BRUTE-FORCE BASELINE (SINGLE-SHOT LLM)</div>
          <div>Prompt: "${prob.prompt}"</div>
        </div>
        <div class="trace-item trace-synthesis">
          <div class="trace-badge" style="color: #00f0ff;">RAW LLM OUTPUT (NO TOOLS / NO RAG)</div>
          <pre>${data.raw_response || JSON.stringify(data, null, 2)}</pre>
          <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #f43f5e;">
            ⚠️ Limitations: 0 Tools Called | No Redfish Verification | No Idempotency | High Hallucination Risk
          </div>
        </div>
      `;
      statusBadge.textContent = 'COMPLETED (BRUTE FORCE)';
      statusBadge.style.color = '#f59e0b';
    } catch (e) {
      statusBadge.textContent = 'ERROR';
      statusBadge.style.color = '#f43f5e';
    }
  }
}

function renderTraceItem(eventObj) {
  const feed = document.getElementById('trace-feed');
  const type = eventObj.event_type;
  const data = eventObj.data;

  let el = document.createElement('div');
  el.className = 'trace-item';

  if (type === 'THOUGHT') {
    el.classList.add('trace-thought');
    el.innerHTML = `
      <div class="trace-badge" style="color: #3b82f6;">🧠 THOUGHT (STEP ${data.step})</div>
      <div>${data.thought}</div>
    `;
  } else if (type === 'ACTION_DISPATCHED') {
    el.classList.add('trace-action');
    el.innerHTML = `
      <div class="trace-badge" style="color: #f59e0b;">🛠️ ACTION: ${data.tool}</div>
      <pre>${JSON.stringify(data.args, null, 2)}</pre>
    `;
  } else if (type === 'OBSERVATION') {
    el.classList.add('trace-observation');
    el.innerHTML = `
      <div class="trace-badge" style="color: #10b981;">👁️ OBSERVATION (${data.duration_ms}ms)</div>
      <pre>${JSON.stringify(data.result, null, 2)}</pre>
    `;
  } else if (type === 'SYNTHESIS') {
    el.classList.add('trace-synthesis');
    el.innerHTML = `
      <div class="trace-badge" style="color: #00f0ff;">💡 SYNTHESIS & RESOLUTION (${data.total_latency_ms}ms)</div>
      <pre>${data.response}</pre>
    `;
  } else if (type === 'TASK_STARTED') {
    el.classList.add('trace-thought');
    el.innerHTML = `
      <div class="trace-badge" style="color: #8b5cf6;">🚀 TASK INITIALIZED: ${data.task_id}</div>
      <div>${data.prompt}</div>
    `;
  }

  feed.appendChild(el);
  feed.scrollTop = feed.scrollHeight;
}

async function fetchFleetTelemetry() {
  try {
    const res = await fetch('/api/telemetry/fleet');
    const data = await res.json();
    const grid = document.getElementById('fleet-grid');
    if (!grid) return;

    grid.innerHTML = data.nodes.map(n => `
      <div class="node-card">
        <div class="node-header">
          <span>${n.server_id}</span>
          <span style="color: ${n.power_state === 'On' ? '#34d399' : '#f43f5e'};">● ${n.power_state}</span>
        </div>
        <div class="node-stat">Model: ${n.model}</div>
        <div class="node-stat">Chassis: ${n.chassis_id}</div>
        <div class="node-stat">VMs: ${n.running_vms} | Drives: ${n.drives_count}</div>
        ${n.critical_drives > 0 ? `<div style="color: #f43f5e; font-size: 0.75rem; font-weight: 600; margin-top: 0.25rem;">⚠️ ${n.critical_drives} Drive Alert</div>` : `<div style="color: #34d399; font-size: 0.75rem; margin-top: 0.25rem;">✓ Health OK</div>`}
      </div>
    `).join('');
  } catch (e) {
    console.error('Fleet telemetry error', e);
  }
}

async function triggerBenchmark() {
  const btn = document.getElementById('btn-run-eval');
  btn.textContent = 'Running Benchmark Suite (50 Scenarios)...';
  try {
    const res = await fetch('/api/evals/benchmark');
    const data = await res.json();
    btn.textContent = '✓ Benchmark Completed! (See Results)';
    setTimeout(() => { btn.textContent = '⚡ Run Comparative Evaluation Benchmark'; }, 3000);
  } catch (e) {
    btn.textContent = 'Benchmark Error';
  }
}

// Initial load
window.addEventListener('DOMContentLoaded', () => {
  fetchFleetTelemetry();
});
