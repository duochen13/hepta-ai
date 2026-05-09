<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { uploadAndAnalyzeCSV } from '../services/codePlaygroundApi'

const emit = defineEmits(['send-message'])

const messages = ref([])
const input = ref('')
const chatMessages = ref(null)
const textarea = ref(null)
const fileInput = ref(null)
const uploadedFile = ref(null)
const isAnalyzing = ref(false)

// Local storage key for chat history
const CHAT_HISTORY_KEY = 'datavint_chat_history'

// Load chat history on mount
onMounted(() => {
  loadChatHistory()
})

// Watch messages and save to localStorage whenever they change
watch(messages, () => {
  saveChatHistory()
}, { deep: true })

function loadChatHistory() {
  try {
    const saved = localStorage.getItem(CHAT_HISTORY_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      messages.value = parsed

      // Scroll to bottom after loading
      nextTick(() => {
        if (chatMessages.value) {
          chatMessages.value.scrollTop = chatMessages.value.scrollHeight
        }
      })
    }
  } catch (error) {
    console.error('Failed to load chat history:', error)
  }
}

function saveChatHistory() {
  try {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages.value))
  } catch (error) {
    console.error('Failed to save chat history:', error)
  }
}

function clearChatHistory() {
  messages.value = []
  localStorage.removeItem(CHAT_HISTORY_KEY)
}

function addMessage(content, type = 'user') {
  messages.value.push({
    content,
    type,
    id: Date.now()
  })

  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  uploadedFile.value = file
  addMessage(`📎 Uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'assistant')
  addMessage('What would you like to analyze? (e.g., "check for missing values", "find duplicates")', 'assistant')
}

async function sendMessage() {
  const message = input.value.trim()
  if (!message) return

  addMessage(message, 'user')
  input.value = ''

  // Reset textarea height
  if (textarea.value) {
    textarea.value.style.height = 'auto'
  }

  // If file is uploaded, analyze it
  if (uploadedFile.value) {
    isAnalyzing.value = true
    addMessage('🔄 Analyzing your dataset...', 'assistant')

    try {
      const result = await uploadAndAnalyzeCSV(uploadedFile.value, message)

      if (result.success) {
        // Show output message
        addMessage(result.output, 'assistant')

        // Show generated code
        if (result.generated_code) {
          addMessage('Generated code:\n```python\n' + result.generated_code + '\n```', 'assistant')
        }

        // Show additional results if available
        if (result.data && result.data.issues) {
          const issueCount = Array.isArray(result.data.issues) ? result.data.issues.length : 0
          if (issueCount > 0) {
            addMessage(`📊 Found ${issueCount} data quality issues. View details in the results panel.`, 'assistant')
          }
        }
      } else {
        // Show error
        addMessage('❌ Analysis failed: ' + (result.error || 'Unknown error'), 'assistant')
      }
    } catch (error) {
      console.error('Analysis error:', error)
      addMessage('❌ Failed to analyze: ' + error.message, 'assistant')
    } finally {
      isAnalyzing.value = false
      uploadedFile.value = null
      // Reset file input
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }
  } else {
    // Normal chat message (no file uploaded)
    emit('send-message', message)
  }
}

function handleKeypress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function handleInput() {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 120) + 'px'
  }
}
</script>

<template>
  <div class="chat-panel">
    <div class="panel-header">
      <div class="panel-title">Assistant</div>
      <div class="header-controls">
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span>READY</span>
        </div>
        <button
          v-if="messages.length > 0"
          class="clear-history-btn"
          @click="clearChatHistory"
          title="Clear chat history"
        >
          🗑️ Clear
        </button>
      </div>
    </div>

    <div ref="chatMessages" class="chat-messages">
      <div class="welcome-message">
        <div class="welcome-title">👋 Welcome to DataVint Playground</div>
        <div class="welcome-text">
          Interactive IDE for exploring data quality detection. Try these commands:
        </div>
        <div class="welcome-commands">
          <div class="welcome-command">Analyze my dataset</div>
          <div class="welcome-command">Show me data quality issues</div>
          <div class="welcome-command">Generate a manifest</div>
          <div class="welcome-command">Compare train vs test data</div>
        </div>
      </div>

      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type]">
        <div class="message-label">{{ msg.type === 'user' ? 'You' : 'DataVint' }}</div>
        <div class="message-content">{{ msg.content }}</div>
      </div>
    </div>

    <div class="chat-input-container">
      <div class="upload-section">
        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          @change="handleFileUpload"
          style="display: none"
        />
        <button
          class="upload-button"
          @click="fileInput.click()"
          :disabled="isAnalyzing"
        >
          📎 Upload CSV
        </button>
        <span v-if="uploadedFile" class="uploaded-filename">
          {{ uploadedFile.name }}
        </span>
      </div>

      <div class="chat-input-wrapper">
        <textarea
          ref="textarea"
          v-model="input"
          class="chat-input"
          :placeholder="uploadedFile ? 'Ask about your dataset...' : 'Ask me about check missing value, duplication rate etc'"
          rows="1"
          @keypress="handleKeypress"
          @input="handleInput"
          :disabled="isAnalyzing"
          autofocus
        ></textarea>
        <button class="send-button" @click="sendMessage" :disabled="isAnalyzing">
          {{ isAnalyzing ? '⏳' : '➤' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-dark);
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.clear-history-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.clear-history-btn:hover {
  background: rgba(255, 82, 82, 0.1);
  border-color: #ff5252;
  color: #ff5252;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--accent-lime);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.welcome-message {
  padding: 24px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.05), rgba(164, 255, 0, 0.05));
  border: 2px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.welcome-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.5;
}

.welcome-commands {
  display: grid;
  gap: 8px;
}

.welcome-command {
  padding: 10px 16px;
  background: var(--bg-dark);
  border: 2px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.2s;
}

.welcome-command:hover {
  background: var(--bg-hover);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  transform: translateX(4px);
}

.message {
  margin-bottom: 16px;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.message.user .message-label {
  color: var(--accent-cyan);
}

.message.assistant .message-label {
  color: var(--accent-lime);
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message.user .message-content {
  background: var(--bg-hover);
  color: var(--text-primary);
  border: 2px solid var(--border);
}

.message.assistant .message-content {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(164, 255, 0, 0.08));
  color: var(--text-primary);
  border: 2px solid var(--border);
}

.chat-input-container {
  padding: 16px;
  border-top: 2px solid var(--border);
  background: var(--bg-dark);
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-button {
  padding: 8px 16px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s;
}

.upload-button:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.upload-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.uploaded-filename {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.chat-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 12px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 14px;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  transition: all 0.2s;
}

.chat-input:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.1);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

/* Animated caret for better focus visibility */
.chat-input:focus {
  caret-color: var(--accent-cyan);
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  50.01%, 100% {
    opacity: 0;
  }
}

.send-button {
  width: 44px;
  height: 44px;
  background: var(--accent-cyan);
  border: 2px solid var(--accent-cyan);
  border-radius: 6px;
  color: var(--bg-dark);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover {
  background: var(--accent-lime);
  border-color: var(--accent-lime);
  transform: translateY(-2px);
}

.send-button:active {
  transform: translateY(0);
}
</style>
