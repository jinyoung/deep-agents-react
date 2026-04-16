<template>
  <div class="app">
    <!-- 왼쪽 사이드바 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Deep Agent</h2>
        <button class="btn-icon" @click="refreshFiles" title="새로고침">&#x21bb;</button>
      </div>

      <div class="sidebar-scroll">
        <!-- ━━ 진행 상황 (Todo) ━━ -->
        <div class="panel" v-if="todos.length">
          <div class="panel-header" @click="panelOpen.todos = !panelOpen.todos">
            <h3>진행 상황</h3>
            <span class="chevron" :class="{ open: panelOpen.todos }">&#9662;</span>
          </div>
          <div v-show="panelOpen.todos" class="panel-body">
            <div v-for="(t, i) in todos" :key="i"
              :class="['todo-item', { done: t.status === 'completed', active: t.status === 'in_progress' }]"
            >
              <span class="todo-check">
                <span v-if="t.status === 'completed'" class="check-done">&#10003;</span>
                <span v-else-if="t.status === 'in_progress'" class="check-active"></span>
                <span v-else class="check-pending"></span>
              </span>
              <span class="todo-text">{{ t.content || t.title || t }}</span>
            </div>
          </div>
        </div>

        <!-- ━━ 컨텍스트 ━━ -->
        <div class="panel" v-if="skills.length || refFiles.length">
          <div class="panel-header" @click="panelOpen.context = !panelOpen.context">
            <h3>컨텍스트</h3>
            <span class="chevron" :class="{ open: panelOpen.context }">&#9662;</span>
          </div>
          <div v-show="panelOpen.context" class="panel-body">
            <div v-if="skills.length" class="ctx-section">
              <div class="ctx-label">스킬</div>
              <div v-for="s in skills" :key="s" class="ctx-item ctx-skill">
                <span class="ctx-icon">S</span>
                <span>{{ s }}</span>
              </div>
            </div>
            <div v-if="refFiles.length" class="ctx-section">
              <div class="ctx-label">참조 파일</div>
              <div v-for="f in refFiles" :key="f" class="ctx-item ctx-ref">
                <span class="ctx-icon">F</span>
                <span>{{ f }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ━━ 파일 ━━ -->
        <div class="panel">
          <div class="panel-header" @click="panelOpen.files = !panelOpen.files">
            <h3>파일</h3>
            <span class="chevron" :class="{ open: panelOpen.files }">&#9662;</span>
          </div>
          <div v-show="panelOpen.files" class="panel-body">
            <!-- 업로드 -->
            <div class="upload-zone"
              @dragover.prevent="dragOver = true"
              @dragleave="dragOver = false"
              @drop.prevent="handleDrop"
              :class="{ 'drag-active': dragOver }"
            >
              <input type="file" ref="fileInput" multiple @change="handleFileSelect" hidden />
              <div @click="$refs.fileInput.click()" class="upload-label">
                <span class="upload-icon">+</span>
                <span>파일 업로드</span>
              </div>
            </div>
            <div v-if="uploadedFiles.length" class="file-list">
              <div class="ctx-label">Uploads</div>
              <div v-for="f in uploadedFiles" :key="f.name" class="file-item">
                <span class="fi-icon fi-upload">U</span>
                <span class="file-name">{{ f.name }}</span>
                <span class="file-size">{{ f.size }}</span>
              </div>
            </div>
            <div v-if="outputFiles.length" class="file-list">
              <div class="ctx-label">Output</div>
              <div v-for="f in outputFiles" :key="f.name" class="file-item file-dl" @click="downloadFile(f.name)">
                <span class="fi-icon fi-output">D</span>
                <span class="file-name">{{ f.name }}</span>
                <span class="file-size">{{ f.size }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="btn-reset" @click="resetSession">새 대화</button>
      </div>
    </aside>

    <!-- 메인 채팅 -->
    <main class="chat-main">
      <div class="chat-messages" ref="chatRef">
        <div v-if="messages.length === 0" class="welcome">
          <h1>Deep Agent Excel</h1>
          <p>엑셀 파일을 만들거나, 파일을 업로드하여 분석/편집을 요청하세요.</p>
          <div class="examples">
            <button v-for="ex in examples" :key="ex" @click="sendMessage(ex)" class="example-btn">{{ ex }}</button>
          </div>
        </div>

        <template v-for="(msg, i) in messages" :key="i">
          <div v-if="msg.role === 'user'" class="msg msg-user">
            <div class="msg-bubble">
              <div class="msg-text">{{ msg.text }}</div>
              <div v-if="msg.files && msg.files.length" class="msg-files">
                <span v-for="f in msg.files" :key="f" class="msg-file-chip">{{ f }}</span>
              </div>
            </div>
          </div>

          <div v-else-if="msg.role === 'assistant'" class="msg msg-assistant">
            <div class="msg-avatar">AI</div>
            <div class="msg-body">
              <template v-for="(step, j) in msg.steps" :key="j">
                <div v-if="step.type === 'token'" class="ai-text">{{ step.text }}</div>
                <div v-else-if="step.type === 'tool_start'" class="tool-block tool-start">
                  <span class="tool-badge">TOOL</span>
                  <code>{{ step.name }}</code>
                  <span v-if="!step.done" class="tool-running">실행 중...</span>
                </div>
                <div v-else-if="step.type === 'tool_result'" class="tool-block tool-result">
                  <details>
                    <summary><code>{{ step.name }}</code> 결과</summary>
                    <pre>{{ step.content }}</pre>
                  </details>
                </div>
              </template>
              <div v-if="msg.files && msg.files.length" class="msg-output-files">
                <button v-for="f in msg.files" :key="f" @click="downloadFile(f)" class="btn-file-dl">{{ f }}</button>
              </div>
            </div>
          </div>
        </template>

        <div v-if="isStreaming" class="msg msg-assistant">
          <div class="msg-avatar">AI</div>
          <div class="msg-body"><span class="typing"><span/><span/><span/></span></div>
        </div>
      </div>

      <div class="chat-input-bar">
        <div class="input-wrapper">
          <textarea ref="inputRef" v-model="inputText" @keydown.enter.exact="onEnter"
            placeholder="메시지를 입력하세요..." :disabled="isStreaming" rows="1" />
          <button @click="send" :disabled="isStreaming || !inputText.trim()" class="btn-send">&#10148;</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const SESSION_ID = 'default'

const messages = ref([])
const inputText = ref('')
const isStreaming = ref(false)
const dragOver = ref(false)
const uploadedFiles = ref([])
const outputFiles = ref([])
const chatRef = ref(null)
const fileInput = ref(null)

// 사이드바 상태
const todos = ref([])
const skills = ref([])
const refFiles = ref([])
const panelOpen = ref({ todos: true, context: true, files: true })

const examples = [
  '2024년 분기별 매출 보고서를 만들어줘',
  '업로드한 파일을 xlsx로 변환해줘',
  '재무제표 템플릿을 만들어줘',
]

function scrollBottom() {
  nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight })
}

// ── 파일 ──
async function uploadFiles(fileList) {
  if (!fileList.length) return []
  const fd = new FormData()
  const names = []
  for (const f of fileList) { fd.append('files', f); names.push(f.name) }
  fd.append('session_id', SESSION_ID)
  await fetch(`${API}/api/upload`, { method: 'POST', body: fd })
  await refreshFiles()
  return names
}
function handleFileSelect(e) { if (e.target.files.length) doUploadAndNotify(e.target.files); e.target.value = '' }
function handleDrop(e) { dragOver.value = false; if (e.dataTransfer.files.length) doUploadAndNotify(e.dataTransfer.files) }
async function doUploadAndNotify(fileList) {
  const names = await uploadFiles(fileList)
  if (names.length) {
    messages.value.push({ role: 'user', text: `파일 업로드: ${names.join(', ')}`, files: names })
    scrollBottom()
  }
}
async function refreshFiles() {
  try {
    const res = await fetch(`${API}/api/files`)
    const data = await res.json()
    uploadedFiles.value = data.uploads || []
    outputFiles.value = data.output || []
  } catch { /* ignore */ }
}
function downloadFile(name) { window.open(`${API}/api/download/${encodeURIComponent(name)}`, '_blank') }

// ── 대화 ──
function onEnter(e) { if (!e.shiftKey) { e.preventDefault(); send() } }
function sendMessage(text) { inputText.value = text; send() }

async function send() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  messages.value.push({ role: 'user', text })
  inputText.value = ''
  scrollBottom()

  messages.value.push({ role: 'assistant', steps: [], files: [] })
  isStreaming.value = true
  const getAiMsg = () => messages.value[messages.value.length - 1]
  let currentTokenIdx = -1

  const url = `${API}/api/stream?prompt=${encodeURIComponent(text)}&session_id=${SESSION_ID}`
  const es = new EventSource(url)

  es.addEventListener('token', (e) => {
    const d = JSON.parse(e.data)
    const aiMsg = getAiMsg()
    if (currentTokenIdx >= 0 && aiMsg.steps[currentTokenIdx]?.type === 'token') {
      aiMsg.steps[currentTokenIdx].text += d.text
    } else {
      currentTokenIdx = aiMsg.steps.length
      aiMsg.steps.push({ type: 'token', text: d.text })
    }
    scrollBottom()
  })

  es.addEventListener('tool_start', (e) => {
    const d = JSON.parse(e.data)
    currentTokenIdx = -1
    getAiMsg().steps.push({ type: 'tool_start', name: d.name, done: false })
    scrollBottom()
  })

  es.addEventListener('tool_result', (e) => {
    const d = JSON.parse(e.data)
    const aiMsg = getAiMsg()
    for (let i = aiMsg.steps.length - 1; i >= 0; i--) {
      if (aiMsg.steps[i].type === 'tool_start' && !aiMsg.steps[i].done) {
        aiMsg.steps[i].done = true
        break
      }
    }
    aiMsg.steps.push({ type: 'tool_result', name: d.name, content: d.content })
    currentTokenIdx = -1
    scrollBottom()
  })

  // ── 사이드바 이벤트 ──
  es.addEventListener('todos', (e) => {
    const d = JSON.parse(e.data)
    todos.value = d.items || []
  })

  es.addEventListener('skill_loaded', (e) => {
    const d = JSON.parse(e.data)
    if (!skills.value.includes(d.name)) skills.value.push(d.name)
  })

  es.addEventListener('ref_file', (e) => {
    const d = JSON.parse(e.data)
    if (!refFiles.value.includes(d.name)) refFiles.value.push(d.name)
  })

  es.addEventListener('status', () => { scrollBottom() })
  es.addEventListener('node_update', () => { scrollBottom() })

  es.addEventListener('done', (e) => {
    const d = JSON.parse(e.data)
    if (d.files && d.files.length) getAiMsg().files = d.files
    isStreaming.value = false
    es.close()
    refreshFiles()
    scrollBottom()
  })

  es.addEventListener('error_event', (e) => {
    const d = JSON.parse(e.data)
    getAiMsg().steps.push({ type: 'token', text: `\n오류: ${d.message}` })
    isStreaming.value = false
    es.close()
    scrollBottom()
  })

  es.onerror = () => { isStreaming.value = false; es.close(); scrollBottom() }
}

async function resetSession() {
  await fetch(`${API}/api/session/reset`, { method: 'POST' })
  messages.value = []
  uploadedFiles.value = []
  outputFiles.value = []
  todos.value = []
  skills.value = []
  refFiles.value = []
}

onMounted(() => { refreshFiles() })
</script>

<style>
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
  --border: #30363d; --text: #e6edf3; --text-muted: #8b949e;
  --accent: #58a6ff; --green: #2ea043; --yellow: #d29922; --purple: #bc8cff;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); }

.app { display: flex; height: 100vh; overflow: hidden; }

/* ━━ 사이드바 ━━ */
.sidebar {
  width: 280px; background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; flex-shrink: 0;
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid var(--border);
}
.sidebar-header h2 { font-size: 1rem; }
.btn-icon {
  background: none; border: 1px solid var(--border); color: var(--text-muted);
  border-radius: 6px; width: 28px; height: 28px; cursor: pointer; font-size: 1rem;
}
.btn-icon:hover { color: var(--text); border-color: var(--text-muted); }

.sidebar-scroll { flex: 1; overflow-y: auto; }
.sidebar-scroll::-webkit-scrollbar { width: 4px; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* 패널 */
.panel { border-bottom: 1px solid var(--border); }
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; cursor: pointer; user-select: none;
}
.panel-header:hover { background: rgba(255,255,255,0.02); }
.panel-header h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }
.chevron { font-size: 0.7rem; color: var(--text-muted); transition: transform 0.2s; }
.chevron.open { transform: rotate(0); }
.chevron:not(.open) { transform: rotate(-90deg); }
.panel-body { padding: 0 12px 12px; }

/* ── Todo ── */
.todo-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 6px 8px; border-radius: 6px; font-size: 0.82rem; line-height: 1.4;
  transition: all 0.3s;
}
.todo-item.active { background: rgba(88,166,255,0.06); }
.todo-check { flex-shrink: 0; width: 18px; height: 18px; margin-top: 1px; display: flex; align-items: center; justify-content: center; }
.check-done {
  width: 18px; height: 18px; border-radius: 50%; background: var(--accent);
  color: white; font-size: 0.65rem; display: flex; align-items: center; justify-content: center;
}
.check-active {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--accent);
  position: relative;
}
.check-active::after {
  content: ''; position: absolute; inset: 3px; border-radius: 50%;
  border: 2px solid var(--accent); border-top-color: transparent;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.check-pending { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--border); }
.todo-item.done .todo-text { text-decoration: line-through; color: var(--text-muted); }
.todo-item.active .todo-text { color: var(--accent); }

/* ── 컨텍스트 ── */
.ctx-section { margin-bottom: 8px; }
.ctx-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.ctx-item {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 8px; border-radius: 6px; font-size: 0.82rem;
  background: var(--surface2); margin-bottom: 3px;
}
.ctx-icon {
  width: 22px; height: 22px; border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; flex-shrink: 0;
}
.ctx-skill .ctx-icon { background: rgba(188,140,255,0.15); color: var(--purple); }
.ctx-ref .ctx-icon { background: rgba(88,166,255,0.15); color: var(--accent); }

/* ── 파일 ── */
.upload-zone {
  border: 2px dashed var(--border); border-radius: 8px; cursor: pointer;
  transition: all 0.2s; margin-bottom: 8px;
}
.upload-zone.drag-active { border-color: var(--accent); background: rgba(88,166,255,0.05); }
.upload-label {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 8px; font-size: 0.82rem; color: var(--text-muted);
}
.upload-icon { color: var(--accent); font-size: 1.1rem; }
.file-list { margin-bottom: 8px; }
.file-item {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 8px; border-radius: 6px; font-size: 0.8rem; overflow: hidden;
}
.file-item:hover { background: rgba(255,255,255,0.03); }
.file-dl { cursor: pointer; }
.file-dl:hover { background: rgba(88,166,255,0.08); }
.fi-icon {
  width: 22px; height: 22px; border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; flex-shrink: 0;
}
.fi-upload { background: rgba(88,166,255,0.15); color: var(--accent); }
.fi-output { background: rgba(46,160,67,0.15); color: var(--green); }
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { color: var(--text-muted); font-size: 0.7rem; flex-shrink: 0; }

.sidebar-footer { padding: 12px; border-top: 1px solid var(--border); }
.btn-reset {
  width: 100%; padding: 8px; background: transparent; border: 1px solid var(--border);
  color: var(--text-muted); border-radius: 8px; font-size: 0.85rem; cursor: pointer;
}
.btn-reset:hover { color: var(--text); border-color: var(--text-muted); }

/* ━━ 채팅 ━━ */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; }
.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

.welcome {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; text-align: center; gap: 12px;
}
.welcome h1 {
  font-size: 1.6rem;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.welcome p { color: var(--text-muted); font-size: 0.95rem; }
.examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; justify-content: center; }
.example-btn {
  padding: 8px 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; color: var(--text); font-size: 0.85rem; cursor: pointer; transition: all 0.2s;
}
.example-btn:hover { border-color: var(--accent); background: rgba(88,166,255,0.06); }

.msg { display: flex; gap: 12px; margin-bottom: 20px; max-width: 800px; margin-left: auto; margin-right: auto; }
.msg-user { justify-content: flex-end; }
.msg-bubble {
  background: #1f6feb; color: white; padding: 10px 16px;
  border-radius: 18px 18px 4px 18px; max-width: 70%; font-size: 0.9rem; line-height: 1.5;
}
.msg-files { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.msg-file-chip { background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; }

.msg-assistant { align-items: flex-start; }
.msg-avatar {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; color: white; flex-shrink: 0;
}
.msg-body {
  flex: 1; min-width: 0; background: var(--surface); border: 1px solid var(--border);
  border-radius: 4px 18px 18px 18px; padding: 12px 16px;
}
.ai-text { font-size: 0.9rem; line-height: 1.7; white-space: pre-wrap; word-break: break-word; }

.tool-block {
  margin: 8px 0; padding: 8px 12px; border-radius: 8px;
  font-size: 0.82rem; display: flex; align-items: center; gap: 8px;
}
.tool-start { background: rgba(210,153,34,0.08); border: 1px solid rgba(210,153,34,0.2); }
.tool-result { background: rgba(46,160,67,0.06); border: 1px solid rgba(46,160,67,0.15); }
.tool-badge {
  background: var(--yellow); color: #000; padding: 1px 6px;
  border-radius: 4px; font-size: 0.65rem; font-weight: 700; flex-shrink: 0;
}
.tool-running { color: var(--yellow); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
.tool-result details summary { cursor: pointer; color: var(--accent); font-size: 0.82rem; }
.tool-result pre {
  background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px; margin-top: 6px; font-size: 0.78rem;
  font-family: 'SF Mono', 'Fira Code', monospace; color: #7ee787;
  white-space: pre-wrap; word-break: break-all; max-height: 250px; overflow-y: auto;
}

.msg-output-files { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.btn-file-dl {
  display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px;
  background: linear-gradient(135deg, #238636, #2ea043); color: white;
  border: none; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-file-dl:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgba(46,160,67,0.3); }

.typing { display: inline-flex; gap: 4px; padding: 4px 0; }
.typing span {
  width: 7px; height: 7px; background: var(--text-muted); border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%,80%,100%{ transform: scale(0.6); opacity: 0.4; } 40%{ transform: scale(1); opacity: 1; } }

.chat-input-bar { padding: 12px 24px 20px; border-top: 1px solid var(--border); background: var(--bg); }
.input-wrapper {
  max-width: 800px; margin: 0 auto; display: flex; gap: 8px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 8px 8px 8px 16px; align-items: flex-end;
}
.input-wrapper textarea {
  flex: 1; background: transparent; border: none; color: var(--text);
  font-size: 0.9rem; font-family: inherit; resize: none; outline: none;
  line-height: 1.5; max-height: 120px; padding: 4px 0;
}
.btn-send {
  width: 36px; height: 36px; background: var(--accent); color: white;
  border: none; border-radius: 10px; font-size: 1.1rem; cursor: pointer;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.btn-send:hover:not(:disabled) { background: #79c0ff; }
.btn-send:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
