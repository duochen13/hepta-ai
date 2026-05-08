<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const hasData = ref(false)
const isLoading = ref(false)
const error = ref(null)
const issues = ref([])
const summary = ref(null)
const datasetId = ref(null)

async function loadIssues() {
  // Get dataset_id from localStorage
  datasetId.value = localStorage.getItem('currentDatasetId')

  console.log('📊 Loading issues for dataset:', datasetId.value)

  if (!datasetId.value) {
    console.warn('⚠️ No dataset_id found in localStorage')
    hasData.value = false
    return
  }

  isLoading.value = true
  error.value = null

  try {
    // Use simple profiling endpoint (works with NumPy 2.0)
    console.log('🔄 Fetching profiling data...')
    const response = await api.profiling.simpleIssues(datasetId.value)
    console.log('✅ Profiling response:', response.data)

    issues.value = response.data.issues
    summary.value = response.data.summary
    hasData.value = issues.value.length > 0 || summary.value.total === 0

    console.log(`📈 Found ${summary.value.total} issues`)
  } catch (err) {
    console.error('❌ Profiling error:', err)
    error.value = err.response?.data?.detail || err.message
    hasData.value = false
  } finally {
    isLoading.value = false
  }
}

function getSeverityIcon(severity) {
  switch (severity) {
    case 'HIGH': return '🔴'
    case 'MEDIUM': return '🟡'
    case 'LOW': return '🟢'
    default: return '⚪'
  }
}

function getSeverityClass(severity) {
  return `severity-${severity.toLowerCase()}`
}

onMounted(() => {
  loadIssues()
})
</script>

<template>
  <div class="visualization-view">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>Analyzing data quality...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Analysis Error</h3>
      <p>{{ error }}</p>
      <router-link to="/data" class="action-link">Upload a new dataset</router-link>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasData" class="empty-state">
      <div class="empty-icon">📈</div>
      <h3>No data to analyze</h3>
      <p>
        Upload a dataset in the <router-link to="/data">Data</router-link> tab to see data quality analysis.
      </p>
    </div>

    <!-- Issues Dashboard -->
    <div v-else class="issues-dashboard">
      <!-- Info Panel -->
      <div class="info-panel">
        <div class="info-header">
          <span class="info-icon">ℹ️</span>
          <h3>Data Quality Severity Levels</h3>
        </div>
        <div class="severity-legend">
          <div class="legend-item">
            <span class="legend-badge high">🔴 HIGH</span>
            <span class="legend-desc">Critical issues - fix before training</span>
          </div>
          <div class="legend-item">
            <span class="legend-badge medium">🟡 MEDIUM</span>
            <span class="legend-desc">Important issues - should address</span>
          </div>
          <div class="legend-item">
            <span class="legend-badge low">🟢 LOW</span>
            <span class="legend-desc">Minor issues - nice to fix</span>
          </div>
        </div>
        <div class="threshold-info">
          <details open>
            <summary>View severity thresholds</summary>
            <ul>
              <li><strong>Missing Values:</strong> HIGH (&gt;60%), MEDIUM (&gt;30%)</li>
              <li><strong>Duplicates:</strong> HIGH (≥30%), MEDIUM (10-30%)</li>
              <li><strong>Class Imbalance:</strong> HIGH (&lt;5% ratio), MEDIUM (&lt;10% ratio)</li>
              <li><strong>Infinite Values:</strong> HIGH (any detected)</li>
              <li><strong>Constant Features:</strong> MEDIUM (100% same value)</li>
              <li><strong>High Cardinality:</strong> LOW (&gt;90% unique)</li>
              <li><strong>Outliers (z&gt;3):</strong> LOW (&gt;5%)</li>
            </ul>
          </details>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="summary-section">
        <div class="summary-card total">
          <div class="card-value">{{ summary.total }}</div>
          <div class="card-label">Total Issues</div>
        </div>
        <div class="summary-card high">
          <div class="card-icon">🔴</div>
          <div class="card-value">{{ summary.high }}</div>
          <div class="card-label">High Severity</div>
        </div>
        <div class="summary-card medium">
          <div class="card-icon">🟡</div>
          <div class="card-value">{{ summary.medium }}</div>
          <div class="card-label">Medium Severity</div>
        </div>
        <div class="summary-card low">
          <div class="card-icon">🟢</div>
          <div class="card-value">{{ summary.low }}</div>
          <div class="card-label">Low Severity</div>
        </div>
      </div>

      <!-- No Issues Found -->
      <div v-if="summary.total === 0" class="no-issues">
        <div class="success-icon">✅</div>
        <h3>No Data Quality Issues Detected!</h3>
        <p>Your dataset looks clean and ready for model training.</p>
      </div>

      <!-- Issues List -->
      <div v-else class="issues-list">
        <h3 class="section-title">Detected Issues</h3>

        <div
          v-for="(issue, index) in issues"
          :key="index"
          class="issue-card"
          :class="getSeverityClass(issue.severity)"
        >
          <div class="issue-header">
            <div class="issue-title">
              <span class="severity-icon">{{ getSeverityIcon(issue.severity) }}</span>
              <span class="issue-type">[{{ issue.type }}]</span>
              <span class="issue-feature">{{ issue.feature || 'Dataset-level' }}</span>
            </div>
            <div class="severity-badge" :class="getSeverityClass(issue.severity)">
              {{ issue.severity }}
            </div>
          </div>

          <div class="issue-description">
            {{ issue.description }}
          </div>

          <div class="issue-metrics">
            <div v-if="issue.metric_value !== null" class="metric">
              <span class="metric-label">Metric Value:</span>
              <span class="metric-value">{{ issue.metric_value.toFixed(4) }}</span>
            </div>
            <div v-if="issue.threshold !== null" class="metric">
              <span class="metric-label">Threshold:</span>
              <span class="metric-value">{{ issue.threshold.toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.visualization-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
  overflow-y: auto;
}

/* Loading State */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border);
  border-top-color: var(--accent-cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  padding: 48px;
  text-align: center;
}

.error-icon {
  font-size: 72px;
  margin-bottom: 24px;
}

.error-state h3 {
  font-size: 20px;
  margin-bottom: 16px;
  color: var(--accent-orange);
}

.error-state p {
  font-size: 14px;
  margin-bottom: 24px;
  color: var(--text-secondary);
}

.action-link {
  padding: 10px 24px;
  background: var(--accent-cyan);
  color: var(--bg-dark);
  border-radius: 6px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.action-link:hover {
  background: var(--accent-lime);
  transform: translateY(-2px);
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  padding: 48px;
  text-align: center;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.empty-state p {
  font-size: 14px;
  line-height: 1.6;
  max-width: 500px;
}

.empty-state a {
  color: var(--accent-cyan);
  font-weight: 600;
}

.empty-state a:hover {
  text-decoration: underline;
}

/* Issues Dashboard */
.issues-dashboard {
  padding: 32px;
}

/* Info Panel */
.info-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 28px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.info-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.info-icon {
  font-size: 22px;
}

.info-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.severity-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-badge {
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.legend-badge.high {
  background: rgba(255, 59, 48, 0.1);
  color: var(--accent-orange);
}

.legend-badge.medium {
  background: rgba(255, 149, 0, 0.1);
  color: #ff9500;
}

.legend-badge.low {
  background: rgba(52, 199, 89, 0.1);
  color: var(--accent-lime);
}

.legend-desc {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 400;
}

.threshold-info {
  margin-top: 12px;
}

.threshold-info details {
  cursor: pointer;
}

.threshold-info summary {
  font-size: 13px;
  color: var(--accent-cyan);
  font-weight: 600;
  user-select: none;
  padding: 8px 0;
}

.threshold-info summary:hover {
  color: var(--accent-lime);
}

.threshold-info ul {
  margin: 12px 0 0 0;
  padding-left: 20px;
  list-style: none;
}

.threshold-info li {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.8;
  font-family: var(--font-mono);
  padding-left: 16px;
  position: relative;
}

.threshold-info li::before {
  content: "▸";
  position: absolute;
  left: 0;
  color: var(--accent-cyan);
}

.threshold-info strong {
  color: var(--text-primary);
}

/* Summary Cards */
.summary-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}

.summary-card {
  padding: 22px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  text-align: center;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.summary-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.summary-card.total {
  background: rgba(0, 122, 255, 0.05);
}

.summary-card.high {
  background: rgba(255, 59, 48, 0.05);
}

.summary-card.medium {
  background: rgba(255, 149, 0, 0.05);
}

.summary-card.low {
  background: rgba(52, 199, 89, 0.05);
}

.card-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.card-value {
  font-size: 34px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  letter-spacing: -0.02em;
}

.card-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* No Issues State */
.no-issues {
  padding: 48px;
  background: rgba(52, 199, 89, 0.05);
  border: 1px solid rgba(52, 199, 89, 0.2);
  border-radius: 16px;
  text-align: center;
}

.success-icon {
  font-size: 56px;
  margin-bottom: 14px;
}

.no-issues h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--accent-lime);
  letter-spacing: -0.01em;
}

.no-issues p {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 400;
}

/* Issues List */
.issues-list {
  margin-top: 28px;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
  letter-spacing: -0.01em;
}

.issue-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 12px;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.issue-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.issue-card.severity-high {
  border-left: 3px solid var(--accent-orange);
}

.issue-card.severity-medium {
  border-left: 3px solid #ff9500;
}

.issue-card.severity-low {
  border-left: 3px solid var(--accent-lime);
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.issue-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.severity-icon {
  font-size: 20px;
}

.issue-type {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.issue-feature {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  letter-spacing: -0.01em;
}

.severity-badge {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
}

.severity-badge.severity-high {
  background: rgba(255, 59, 48, 0.1);
  color: var(--accent-orange);
}

.severity-badge.severity-medium {
  background: rgba(255, 149, 0, 0.1);
  color: #ff9500;
}

.severity-badge.severity-low {
  background: rgba(52, 199, 89, 0.1);
  color: var(--accent-lime);
}

.issue-description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
  font-size: 14px;
}

.issue-metrics {
  display: flex;
  gap: 24px;
  font-size: 13px;
  font-family: var(--font-mono);
}

.metric {
  display: flex;
  gap: 8px;
}

.metric-label {
  color: var(--text-muted);
}

.metric-value {
  color: var(--accent-cyan);
  font-weight: 600;
}
</style>
