/* ===== AlphaQ Frontend App ===== */

const API_BASE = '';
let sessionId = generateId();
let isLoading = false;

// ---- DOM refs ----
const chatWindow    = document.getElementById('chatWindow');
const messageInput  = document.getElementById('messageInput');
const sendBtn       = document.getElementById('sendBtn');
const contextInput  = document.getElementById('contextInput');
const sessionDisplay= document.getElementById('sessionDisplay');
const providerBadge = document.getElementById('providerBadge');
const modelBadge    = document.getElementById('modelBadge');
const statusDot     = document.getElementById('statusDot');
const statusText    = document.getElementById('statusText');
const newSessionBtn = document.getElementById('newSessionBtn');
const clearSessionBtn=document.getElementById('clearSessionBtn');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar       = document.getElementById('sidebar');

// ---- Utilities ----
function generateId() {
  return 'alphaq-' + Math.random().toString(36).slice(2, 10);
}

function shortId(id) {
  return id.length > 20 ? id.slice(0, 20) + '...' : id;
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ---- Marked config ----
marked.setOptions({
  breaks: true,
  gfm: true,
});

// ---- Health check ----
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    statusDot.className = 'status-dot online';
    statusText.textContent = 'Online';
    providerBadge.textContent = data.provider.toUpperCase();
    modelBadge.textContent = data.model;
  } catch {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Offline';
    providerBadge.textContent = 'Disconnected';
    modelBadge.textContent = '';
  }
}

// ---- Step tracker ----
const STEP_MAP = {
  '1. Macro Context':           'step1',
  '2. Multi-Timeframe Analysis':'step2',
  '3. Smart Money & On-Chain':  'step3',
  '4. Trade Construction':      'step4',
  '5. Risk Management':         'step5',
};

function resetSteps() {
  Object.values(STEP_MAP).forEach(id => {
    document.getElementById(id).classList.remove('active');
  });
}

function highlightSteps(steps) {
  resetSteps();
  steps.forEach(step => {
    const id = STEP_MAP[step];
    if (id) document.getElementById(id).classList.add('active');
  });
}

// ---- Render messages ----
function appendMessage(role, content, meta = {}) {
  const msg = document.createElement('div');
  msg.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'U' : '\u25b2';

  const right = document.createElement('div');
  right.style.flex = '1';
  right.style.minWidth = '0';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  if (role === 'assistant') {
    bubble.innerHTML = marked.parse(content);
  } else {
    bubble.textContent = content;
  }

  right.appendChild(bubble);

  // Meta row
  if (meta.timestamp || meta.steps?.length) {
    const metaRow = document.createElement('div');
    metaRow.className = 'msg-meta';
    if (meta.timestamp) {
      const t = document.createElement('span');
      t.textContent = meta.timestamp;
      metaRow.appendChild(t);
    }
    if (meta.provider) {
      const p = document.createElement('span');
      p.textContent = meta.provider;
      metaRow.appendChild(p);
    }
    (meta.steps || []).forEach(step => {
      const tag = document.createElement('span');
      tag.className = 'step-tag';
      tag.textContent = step.replace(/^\d+\.\s*/, '');
      metaRow.appendChild(tag);
    });
    right.appendChild(metaRow);
  }

  msg.appendChild(avatar);
  msg.appendChild(right);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return msg;
}

function appendTyping() {
  const msg = document.createElement('div');
  msg.className = 'message assistant';
  msg.id = 'typingMsg';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = '\u25b2';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return msg;
}

function removeTyping() {
  const el = document.getElementById('typingMsg');
  if (el) el.remove();
}

// ---- Welcome screen ----
function showWelcome() {
  chatWindow.innerHTML = '';
  resetSteps();
  const card = document.createElement('div');
  card.className = 'welcome-card';
  card.innerHTML = `
    <div class="welcome-icon">&#9650;</div>
    <div class="welcome-title">Project AlphaQ</div>
    <div class="welcome-sub">
      Institutional-grade crypto trading intelligence.<br/>
      Powered by the 5-step analysis hierarchy.
    </div>
    <div class="welcome-steps">
      <div class="welcome-step"><div class="welcome-step-num">1</div><span><strong>Macro Context</strong> &mdash; Fed, DXY, ETF flows, halving, stablecoin supply</span></div>
      <div class="welcome-step"><div class="welcome-step-num">2</div><span><strong>Multi-Timeframe</strong> &mdash; Monthly &rarr; 5M with higher TF context first</span></div>
      <div class="welcome-step"><div class="welcome-step-num">3</div><span><strong>Smart Money &amp; On-Chain</strong> &mdash; OBs, FVGs, CHoCH, whale moves, liquidations</span></div>
      <div class="welcome-step"><div class="welcome-step-num">4</div><span><strong>Trade Construction</strong> &mdash; Entry, SL, TP1-3, R:R, probability, invalidation</span></div>
      <div class="welcome-step"><div class="welcome-step-num">5</div><span><strong>Risk Management</strong> &mdash; Position sizing, funding decay, slippage</span></div>
    </div>
    <div class="welcome-disclaimer">⚠️ For educational purposes only. Not financial advice. Always do your own research.</div>
  `;
  chatWindow.appendChild(card);
}

// ---- Send message ----
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || isLoading) return;

  const context = contextInput.value.trim() || undefined;

  // Clear welcome if present
  const welcome = chatWindow.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  appendMessage('user', text, { timestamp: now() });
  messageInput.value = '';
  autoResize();

  isLoading = true;
  sendBtn.disabled = true;
  const typing = appendTyping();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: sessionId,
        context: context,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    removeTyping();

    appendMessage('assistant', data.response, {
      timestamp: now(),
      steps: data.analysis_steps,
      provider: data.provider,
    });

    highlightSteps(data.analysis_steps);

  } catch (err) {
    removeTyping();
    appendMessage('assistant',
      `**Error:** ${err.message}\n\nMake sure the AlphaQ server is running and your API key is configured.`,
      { timestamp: now() }
    );
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Error';
  } finally {
    isLoading = false;
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

// ---- Session management ----
function updateSessionDisplay() {
  sessionDisplay.textContent = shortId(sessionId);
}

newSessionBtn.addEventListener('click', () => {
  sessionId = generateId();
  updateSessionDisplay();
  showWelcome();
  resetSteps();
});

clearSessionBtn.addEventListener('click', async () => {
  try {
    await fetch(`${API_BASE}/session/${sessionId}`, { method: 'DELETE' });
  } catch {}
  showWelcome();
  resetSteps();
});

// ---- Quick queries ----
document.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    messageInput.value = btn.dataset.q;
    autoResize();
    messageInput.focus();
    // On mobile, close sidebar
    sidebar.classList.remove('open');
  });
});

// ---- Sidebar toggle ----
sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('open');
});

// ---- Auto-resize textarea ----
function autoResize() {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + 'px';
}
messageInput.addEventListener('input', autoResize);

// ---- Keyboard shortcuts ----
messageInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

// ---- Init ----
updateSessionDisplay();
showWelcome();
checkHealth();
setInterval(checkHealth, 30000);
messageInput.focus();
