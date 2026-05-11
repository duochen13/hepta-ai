<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import DataCommitNode from '../components/DataCommitNode.vue'
import ModelRunNode from '../components/ModelRunNode.vue'
import LineageGraph from '../components/LineageGraph.vue'

const route = useRoute()

// Experiment data
const experimentId = computed(() => route.params.experimentId || 'test_learning_rate_experiment')
const dataCommits = ref([])
const modelRuns = ref([])
const connections = ref({})
const loading = ref(true)
const error = ref(null)

// Fetch experiment lineage from API
async function fetchExperimentLineage() {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`/api/experiments/${experimentId.value}/lineage`)

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
    loadMockData()
    error.value = null // Clear error so v-else renders the graph
  } finally {
    loading.value = false
  }
}

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
  fetchExperimentLineage()
})
</script>

<template>
  <div class="experiment-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading experiment lineage...</p>
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
