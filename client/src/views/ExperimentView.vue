<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DataCommitNode from '../components/DataCommitNode.vue'
import ModelRunNode from '../components/ModelRunNode.vue'
import LineageGraph from '../components/LineageGraph.vue'

const route = useRoute()
const router = useRouter()

// Experiment data
const experimentId = computed(() => route.params.experimentId || 'test_learning_rate_experiment')
const dataCommits = ref([])
const modelRuns = ref([])
const connections = ref({})
const loading = ref(true)
const error = ref(null)

// Mode toggle: 'sdk' or 'cli'
const mode = ref(route.query.mode || 'sdk')

// CLI experiments list
const cliExperiments = ref([])
const selectedCliFingerprint = ref(null)

// Fetch experiment lineage from API
async function fetchExperimentLineage() {
  loading.value = true
  error.value = null

  try {
    let response

    if (mode.value === 'cli') {
      // Fetch CLI experiment lineage
      const fingerprint = selectedCliFingerprint.value || experimentId.value
      response = await fetch(`/api/cli-experiments/${fingerprint}/lineage`)
    } else {
      // Fetch SDK experiment lineage
      response = await fetch(`/api/experiments/${experimentId.value}/lineage`)
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

    dataCommits.value = data.dataCommits || []
    modelRuns.value = data.modelRuns || []
    connections.value = data.connections || {}
  } catch (err) {
    console.error('Failed to fetch experiment lineage:', err)

    // Load mock data for development (and clear error so graph renders)
    if (mode.value === 'sdk') {
      loadMockData()
      error.value = null // Clear error so v-else renders the graph
    } else {
      error.value = `Failed to fetch CLI experiments. Make sure you have run 'datavint check' first.`
    }
  } finally {
    loading.value = false
  }
}

// Fetch CLI experiments list
async function fetchCliExperiments() {
  try {
    const response = await fetch('/api/cli-experiments/list?limit=20')
    if (response.ok) {
      const data = await response.json()
      cliExperiments.value = data.experiments || []

      // Select first experiment if none selected
      if (cliExperiments.value.length > 0 && !selectedCliFingerprint.value) {
        selectedCliFingerprint.value = cliExperiments.value[0].fingerprint
      }
    }
  } catch (err) {
    console.error('Failed to fetch CLI experiments list:', err)
  }
}

// Toggle mode
function toggleMode(newMode) {
  mode.value = newMode
  router.push({ query: { ...route.query, mode: newMode } })

  if (newMode === 'cli') {
    fetchCliExperiments().then(() => fetchExperimentLineage())
  } else {
    fetchExperimentLineage()
  }
}

// Watch for selected CLI experiment changes
watch(selectedCliFingerprint, () => {
  if (mode.value === 'cli') {
    fetchExperimentLineage()
  }
})

// Mock data for development (based on dashboard mockup)
// Winner Selection Logic:
//   - Overall Best: Lowest NE across all model runs (M0: 0.685)
//   - Sweep Winner: Lowest NE within that sweep
//   - Lower NE (Normalized Entropy) = better model performance
function loadMockData() {
  dataCommits.value = [
    {
      id: 'D1',
      message: 'fix user feature coverage',
      hash: 'a3f9d2c',
      rowCount: 1200000,
      timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
    },
    {
      id: 'D0',
      message: 'dedup interactions',
      hash: '7b2e8f1',
      rowCount: 1500000,
      timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
    },
  ]

  modelRuns.value = [
    {
      id: 'M2.2',
      dataCommitId: 'D1',
      message: 'sample_rate=0.6',
      metrics: {
        NE: { value: 0.701, quality: 'ok' },
        CTR: { value: 0.0058, quality: 'good' },
        lr: { value: 0.005, quality: 'neutral' },
        coverage: { value: '94%', quality: 'good' },
      },
      timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
      sweepWinner: true,
      sweep: { id: 2, name: 'Sample Rate (from D1, lr=0.005)' },
    },
    {
      id: 'M2.1',
      dataCommitId: 'D1',
      message: 'sample_rate=0.4',
      metrics: {
        NE: { value: 0.723, quality: 'bad' },
        CTR: { value: 0.0051, quality: 'ok' },
        lr: { value: 0.005, quality: 'neutral' },
        coverage: { value: '89%', quality: 'ok' },
      },
      timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
      sweep: { id: 2, name: 'Sample Rate (from D1, lr=0.005)' },
    },
    {
      id: 'M2',
      dataCommitId: 'D0',
      message: 'lr=0.005 ← selected for Sweep 2',
      metrics: {
        NE: { value: 0.712, quality: 'ok' },
        CTR: { value: 0.0053, quality: 'good' },
      },
      timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
      sweep: { id: 1, name: 'Learning Rate (from D0)' },
    },
    {
      id: 'M3',
      dataCommitId: 'D0',
      message: 'lr=0.010',
      metrics: {
        NE: { value: 0.734, quality: 'bad' },
        CTR: { value: 0.0047, quality: 'neutral' },
      },
      timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
      sweep: { id: 1, name: 'Learning Rate (from D0)' },
    },
    {
      id: 'M1',
      dataCommitId: 'D0',
      message: 'lr=0.020',
      metrics: {
        NE: { value: 0.698, quality: 'ok' },
        CTR: { value: 0.0042, quality: 'neutral' },
      },
      timestamp: new Date(Date.now() - 6 * 3600000).toISOString(),
      sweepWinner: true,
      sweep: { id: 1, name: 'Learning Rate (from D0)' },
    },
    {
      id: 'M0',
      dataCommitId: 'D0',
      message: 'lr=0.030',
      metrics: {
        NE: { value: 0.685, quality: 'good' },
        CTR: { value: 0.0039, quality: 'neutral' },
      },
      timestamp: new Date(Date.now() - 6 * 3600000).toISOString(),
      best: true,
      sweep: { id: 1, name: 'Learning Rate (from D0)' },
    },
  ]

  connections.value = {
    'D1': ['M2.2', 'M2.1'],
    'D0': ['M3', 'M2', 'M1', 'M0'],
  }
}

// Format timestamp for display
function formatTimestamp(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

// Group model runs by sweep
const modelRunsBySweep = computed(() => {
  const sweeps = {}

  modelRuns.value.forEach(run => {
    if (!run.sweep) return

    const sweepId = run.sweep.id
    if (!sweeps[sweepId]) {
      sweeps[sweepId] = {
        id: sweepId,
        name: run.sweep.name,
        runs: [],
      }
    }
    sweeps[sweepId].runs.push(run)
  })

  // Sort sweeps descending (newest first)
  return Object.values(sweeps).sort((a, b) => b.id - a.id)
})

onMounted(() => {
  if (mode.value === 'cli') {
    fetchCliExperiments().then(() => fetchExperimentLineage())
  } else {
    fetchExperimentLineage()
  }
})
</script>

<template>
  <div class="experiment-view">
    <!-- Mode Toggle Header -->
    <div class="mode-toggle-header">
      <div class="mode-buttons">
        <button
          class="mode-btn"
          :class="{ active: mode === 'sdk' }"
          @click="toggleMode('sdk')"
        >
          📦 SDK Experiments
        </button>
        <button
          class="mode-btn"
          :class="{ active: mode === 'cli' }"
          @click="toggleMode('cli')"
        >
          💻 CLI Experiments
        </button>
      </div>

      <!-- CLI Experiment Selector -->
      <div v-if="mode === 'cli' && cliExperiments.length > 0" class="cli-selector">
        <label for="cli-experiment-select">Select Experiment:</label>
        <select
          id="cli-experiment-select"
          v-model="selectedCliFingerprint"
          class="cli-select"
        >
          <option
            v-for="exp in cliExperiments"
            :key="exp.fingerprint"
            :value="exp.fingerprint"
          >
            {{ exp.fingerprint.substring(0, 8) }} - {{ exp.datasetPath.split('/').pop() }}
            ({{ exp.rowCount.toLocaleString() }} rows)
            {{ exp.outcome ? ` - ${exp.outcome.status}` : '' }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading experiment lineage...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <p v-if="mode === 'cli'" class="error-hint">
        Run <code>datavint check your_dataset.csv</code> to create CLI experiments.
      </p>
    </div>

    <!-- Experiment Lineage Graph -->
    <div v-else class="graph-container">
      <LineageGraph
        :data-commits="dataCommits"
        :model-runs="modelRuns"
        :connections="connections"
      />

      <!-- Comparison Panel -->
      <aside class="comparison-panel">
        <div class="comparison-title">🎯 Experiment Flow</div>
        <div class="comparison-insight">
          <strong>Sweep 1:</strong> Tried 4 learning rates on D0 (deduped data). M1 (lr=0.020) achieved lowest NE (0.698), but M0 (lr=0.030) achieved <strong>0.685 NE</strong> — the overall best performance.<br><br>
          <strong>Sweep 2:</strong> Fixed lr=0.005 from M1, moved to D1 (better feature coverage), swept sample_rate. M2.2 (sample_rate=0.6) achieved <strong>0.701 NE</strong> — winning Sweep 2 with improved data quality.
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.experiment-view {
  height: 100%;
  overflow: auto;
  background: var(--bg-primary);
  padding: 32px;
}

/* Mode Toggle Header */
.mode-toggle-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-panel);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.mode-buttons {
  display: flex;
  gap: 12px;
}

.mode-btn {
  padding: 10px 20px;
  background: transparent;
  border: 2px solid var(--border);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--text-primary);
}

.mode-btn.active {
  background: var(--accent-cyan);
  border-color: var(--accent-cyan);
  color: white;
}

.cli-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cli-selector label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.cli-select {
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-mono);
  min-width: 400px;
  cursor: pointer;
}

.cli-select:focus {
  outline: none;
  border-color: var(--accent-cyan);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent-cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-secondary);
}

.error-icon {
  font-size: 48px;
  margin: 0;
}

.error-hint {
  margin-top: 16px;
  padding: 12px 24px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
}

.error-hint code {
  font-family: var(--font-mono);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--accent-cyan);
}

.error-message {
  font-size: 14px;
  color: var(--text-error);
  margin: 0;
}

.error-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0;
}

/* Graph Container */
.graph-container {
  position: relative;
  min-height: 600px;
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 48px;
  border: 1px solid var(--border);
}

/* Comparison Panel */
.comparison-panel {
  margin-top: 24px;
  padding: 20px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 8px;
}

.comparison-title {
  font-size: 13px;
  font-weight: 600;
  color: #FCD34D;
  margin-bottom: 12px;
}

.comparison-insight {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.comparison-insight strong {
  color: var(--text-primary);
}
</style>
