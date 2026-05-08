<script setup>
import { ref, onMounted } from 'vue'
import Editor from '@monaco-editor/react'
import { executeTemplate, listTemplates } from '../services/codePlaygroundApi'

// State
const templates = ref([])
const selectedTemplate = ref(null)
const isExecuting = ref(false)
const results = ref(null)
const error = ref(null)

// Load templates on mount
onMounted(async () => {
  try {
    console.log('[CodePlayground] Fetching templates...')
    const response = await listTemplates()
    console.log('[CodePlayground] Response:', response)
    templates.value = response.templates
    console.log('[CodePlayground] Templates loaded:', templates.value)
    if (templates.value.length > 0) {
      selectedTemplate.value = templates.value[0]
    }

    // Restore previous results from localStorage
    const savedResults = localStorage.getItem('codePlaygroundResults')
    const savedTemplate = localStorage.getItem('codePlaygroundTemplate')
    if (savedResults) {
      try {
        results.value = JSON.parse(savedResults)
        console.log('[CodePlayground] Restored previous results from localStorage')
      } catch (e) {
        console.error('[CodePlayground] Failed to parse saved results:', e)
      }
    }
    if (savedTemplate && templates.value.length > 0) {
      const saved = templates.value.find(t => t.id === savedTemplate)
      if (saved) {
        selectedTemplate.value = saved
      }
    }
  } catch (err) {
    console.error('[CodePlayground] Failed to load templates:', err)
    console.error('[CodePlayground] Error details:', err.response?.data || err.message)
    error.value = 'Failed to load code templates'
  }
})

// Execute template
async function handleRun() {
  if (!selectedTemplate.value) return

  isExecuting.value = true
  error.value = null
  results.value = null

  try {
    const response = await executeTemplate(selectedTemplate.value.id)
    if (response.success) {
      results.value = response.data

      // Save results to localStorage for persistence
      localStorage.setItem('codePlaygroundResults', JSON.stringify(response.data))
      localStorage.setItem('codePlaygroundTemplate', selectedTemplate.value.id)
      console.log('[CodePlayground] Results saved to localStorage')
    } else {
      error.value = response.error || 'Execution failed'
    }
  } catch (err) {
    console.error('Execution error:', err)
    if (err.response?.status === 429) {
      error.value = 'Rate limit exceeded. Please wait a minute and try again.'
    } else {
      error.value = err.response?.data?.detail || 'An error occurred during execution'
    }
  } finally {
    isExecuting.value = false
  }
}

// Select template
function selectTemplate(template) {
  selectedTemplate.value = template
  results.value = null
  error.value = null

  // Clear saved results when changing templates
  localStorage.removeItem('codePlaygroundResults')
  localStorage.removeItem('codePlaygroundTemplate')
}
</script>

<template>
  <div class="code-playground">
    <!-- Header with template selector -->
    <div class="playground-header">
      <div class="template-selector">
        <label>Template:</label>
        <select v-model="selectedTemplate" @change="selectTemplate(selectedTemplate)">
          <option v-for="template in templates" :key="template.id" :value="template">
            {{ template.name }}
          </option>
        </select>
      </div>
      <button
        class="run-button"
        @click="handleRun"
        :disabled="isExecuting || !selectedTemplate"
      >
        {{ isExecuting ? 'Running...' : 'Run' }}
      </button>
    </div>

    <!-- Template description -->
    <div v-if="selectedTemplate" class="template-description">
      {{ selectedTemplate.description }}
    </div>

    <!-- Code editor -->
    <div class="editor-section">
      <Editor
        v-if="selectedTemplate"
        height="400px"
        language="python"
        theme="vs-dark"
        :value="selectedTemplate.code"
        :options="{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true
        }"
      />
      <div v-else class="loading">
        Loading templates...
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="isExecuting" class="execution-status">
      <div class="spinner"></div>
      <span>Executing code...</span>
    </div>

    <!-- Error display -->
    <div v-if="error" class="error-message">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Results display -->
    <div v-if="results && !isExecuting" class="results-section">
      <h3>Results</h3>

      <!-- Summary stats -->
      <div class="results-summary">
        <div class="stat-card">
          <div class="stat-label">Rows</div>
          <div class="stat-value">{{ results.summary.num_rows }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Columns</div>
          <div class="stat-value">{{ results.summary.num_columns }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Issues Found</div>
          <div class="stat-value" :class="{ 'error-count': results.summary.num_issues > 0 }">
            {{ results.summary.num_issues }}
          </div>
        </div>
      </div>

      <!-- Issues breakdown -->
      <div v-if="results.summary.num_issues > 0" class="issues-breakdown">
        <h4>Issues by Severity</h4>
        <div class="severity-list">
          <div v-if="results.summary.severity_counts.high > 0" class="severity-item high">
            High: {{ results.summary.severity_counts.high }}
          </div>
          <div v-if="results.summary.severity_counts.medium > 0" class="severity-item medium">
            Medium: {{ results.summary.severity_counts.medium }}
          </div>
          <div v-if="results.summary.severity_counts.low > 0" class="severity-item low">
            Low: {{ results.summary.severity_counts.low }}
          </div>
        </div>
      </div>

      <!-- Detailed issues -->
      <div v-if="results.issues.length > 0" class="issues-details">
        <h4>Detected Issues</h4>
        <div class="issues-list">
          <div v-for="(issue, index) in results.issues.slice(0, 10)" :key="index" class="issue-card">
            <div class="issue-header">
              <span class="issue-severity" :class="issue.severity.toLowerCase()">
                {{ issue.severity }}
              </span>
              <span class="issue-type">{{ issue.type }}</span>
            </div>
            <div class="issue-description">{{ issue.description }}</div>
          </div>
          <div v-if="results.issues.length > 10" class="more-issues">
            ... and {{ results.issues.length - 10 }} more issues
          </div>
        </div>
      </div>

      <!-- Success message if no issues -->
      <div v-else class="success-message">
        ✅ No data quality issues detected!
      </div>
    </div>
  </div>
</template>

<style scoped>
.code-playground {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  padding: 20px;
  background: var(--bg-dark);
}

.playground-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bg-panel);
  border-radius: 8px;
  border: 2px solid var(--border);
}

.template-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-selector label {
  font-weight: 600;
  color: var(--text-primary);
}

.template-selector select {
  padding: 8px 12px;
  border: 2px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-dark);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.template-selector select:hover {
  border-color: var(--accent-cyan);
}

.run-button {
  padding: 10px 24px;
  background: var(--accent-cyan);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.run-button:hover:not(:disabled) {
  background: var(--accent-lime);
  transform: translateY(-2px);
}

.run-button:disabled {
  background: var(--bg-hover);
  color: var(--text-muted);
  cursor: not-allowed;
}

.template-description {
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.1);
  border-left: 4px solid var(--accent-cyan);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 14px;
}

.editor-section {
  background: var(--bg-panel);
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid var(--border);
}

.loading {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
}

.execution-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #e3f2fd;
  border-radius: 8px;
  color: #1976d2;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #e3f2fd;
  border-top-color: #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 16px;
  background: #ffebee;
  border-left: 4px solid #f44336;
  border-radius: 4px;
  color: #c62828;
}

.results-section {
  background: var(--bg-panel);
  border-radius: 8px;
  padding: 20px;
  border: 2px solid var(--border);
}

.results-section h3 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 16px;
  background: var(--bg-hover);
  border-radius: 8px;
  text-align: center;
  border: 2px solid var(--border);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.error-count {
  color: var(--accent-orange);
}

.issues-breakdown {
  margin-bottom: 24px;
}

.issues-breakdown h4 {
  margin: 0 0 12px 0;
  color: var(--text-primary);
  font-size: 16px;
}

.severity-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.severity-item {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
}

.severity-item.critical {
  background: rgba(220, 38, 38, 0.2);
  color: var(--accent-orange);
  border: 2px solid var(--accent-orange);
}

.severity-item.high {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
  border: 2px solid #ff9800;
}

.severity-item.medium {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 2px solid #ffc107;
}

.severity-item.low {
  background: rgba(99, 102, 241, 0.2);
  color: var(--accent-cyan);
  border: 2px solid var(--accent-cyan);
}

.issues-details h4 {
  margin: 0 0 12px 0;
  color: var(--text-primary);
  font-size: 16px;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-card {
  padding: 12px;
  background: var(--bg-hover);
  border-radius: 6px;
  border: 2px solid var(--border);
  border-left-width: 4px;
}

.issue-card .severity-item.critical,
.issue-card.critical {
  border-left-color: var(--accent-orange);
}

.issue-card .severity-item.high,
.issue-card.high {
  border-left-color: #ff9800;
}

.issue-card .severity-item.medium,
.issue-card.medium {
  border-left-color: #ffc107;
}

.issue-card .severity-item.low,
.issue-card.low {
  border-left-color: var(--accent-cyan);
}

.issue-header {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.issue-severity {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.issue-severity.critical {
  background: rgba(220, 38, 38, 0.2);
  color: var(--accent-orange);
  border: 1px solid var(--accent-orange);
}

.issue-severity.high {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
  border: 1px solid #ff9800;
}

.issue-severity.medium {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 1px solid #ffc107;
}

.issue-severity.low {
  background: rgba(99, 102, 241, 0.2);
  color: var(--accent-cyan);
  border: 1px solid var(--accent-cyan);
}

.issue-type {
  color: var(--text-muted);
  font-size: 12px;
}

.issue-description {
  color: var(--text-primary);
  font-size: 14px;
}

.more-issues {
  padding: 12px;
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}

.success-message {
  padding: 16px;
  background: rgba(16, 185, 129, 0.2);
  border-left: 4px solid var(--accent-lime);
  border-radius: 4px;
  color: var(--accent-lime);
  font-size: 16px;
}
</style>
