<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import DataCommitNode from './DataCommitNode.vue'
import ModelRunNode from './ModelRunNode.vue'

const props = defineProps({
  dataCommits: {
    type: Array,
    required: true,
  },
  modelRuns: {
    type: Array,
    required: true,
  },
  connections: {
    type: Object,
    required: true,
  },
})

// Active nodes for highlighting
const activeDataNodes = ref(new Set())
const activeModelNodes = ref(new Set())

// SVG paths for connections
const svgPaths = ref([])
const graphContainer = ref(null)
const svgElement = ref(null)

// Group model runs by sweep
const modelRunsBySweep = computed(() => {
  const sweeps = {}

  props.modelRuns.forEach(run => {
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

// Handle node hover
function handleDataNodeHover(nodeId, isHovering) {
  if (isHovering) {
    activeDataNodes.value.add(nodeId)
    // Highlight connected model nodes
    const connectedModels = props.connections[nodeId] || []
    connectedModels.forEach(modelId => activeModelNodes.value.add(modelId))
  } else {
    activeDataNodes.value.clear()
    activeModelNodes.value.clear()
  }
  drawConnections()
}

function handleModelNodeHover(nodeId, isHovering) {
  if (isHovering) {
    activeModelNodes.value.add(nodeId)
    // Find which data node connects to this model
    Object.keys(props.connections).forEach(dataId => {
      if (props.connections[dataId].includes(nodeId)) {
        activeDataNodes.value.add(dataId)
      }
    })
  } else {
    activeDataNodes.value.clear()
    activeModelNodes.value.clear()
  }
  drawConnections()
}

// Get node center coordinates for SVG connections
function getNodeCenter(nodeId) {
  const node = document.querySelector(`[data-id="${nodeId}"]`)
  if (!node || !graphContainer.value) return null

  const nodeRect = node.getBoundingClientRect()
  const containerRect = graphContainer.value.getBoundingClientRect()

  return {
    x: nodeRect.left - containerRect.left + nodeRect.width / 2,
    y: nodeRect.top - containerRect.top + nodeRect.height / 2,
  }
}

// Draw SVG connection lines
function drawConnections() {
  if (!graphContainer.value || !svgElement.value) return

  const paths = []
  const containerRect = graphContainer.value.getBoundingClientRect()

  // Set SVG dimensions
  svgElement.value.setAttribute('width', containerRect.width)
  svgElement.value.setAttribute('height', containerRect.height)

  // Draw all connections
  Object.keys(props.connections).forEach(dataId => {
    const dataCenter = getNodeCenter(dataId)
    if (!dataCenter) return

    props.connections[dataId].forEach(modelId => {
      const modelCenter = getNodeCenter(modelId)
      if (!modelCenter) return

      // Bezier curve
      const midX = (dataCenter.x + modelCenter.x) / 2

      const path = {
        d: `M ${dataCenter.x} ${dataCenter.y}
            C ${midX} ${dataCenter.y}, ${midX} ${modelCenter.y}, ${modelCenter.x} ${modelCenter.y}`,
        classes: {
          active: activeDataNodes.value.has(dataId) && activeModelNodes.value.has(modelId),
          best: modelId === 'M2.2', // Best model gets highlighted
        },
        from: dataId,
        to: modelId,
      }

      paths.push(path)
    })
  })

  svgPaths.value = paths
}

// Debounce helper
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Redraw on resize
const debouncedRedraw = debounce(drawConnections, 150)

onMounted(async () => {
  await nextTick()
  drawConnections()
  window.addEventListener('resize', debouncedRedraw)
})
</script>

<template>
  <div ref="graphContainer" class="lineage-graph">
    <!-- SVG for connections -->
    <svg
      ref="svgElement"
      class="connections"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        v-for="(path, index) in svgPaths"
        :key="index"
        :d="path.d"
        class="connection-line"
        :class="{ active: path.classes.active, best: path.classes.best }"
        :data-from="path.from"
        :data-to="path.to"
      />
    </svg>

    <!-- Graph Layout: Two Columns -->
    <div class="graph">
      <!-- Left: Data Commits -->
      <section class="branch">
        <h2 class="branch-label">Data Commits</h2>
        <div class="nodes">
          <DataCommitNode
            v-for="commit in dataCommits"
            :key="commit.id"
            :commit="commit"
            :active="activeDataNodes.has(commit.id)"
            @hover="handleDataNodeHover"
          />
        </div>
      </section>

      <!-- Right: Model Runs (Grouped by Sweep) -->
      <section class="branch">
        <h2 class="branch-label">Model Runs</h2>
        <div class="nodes">
          <!-- Sweep Clusters -->
          <div
            v-for="sweep in modelRunsBySweep"
            :key="sweep.id"
            class="sweep-cluster"
            role="group"
            :aria-label="`Sweep ${sweep.id}: ${sweep.name}`"
          >
            <div class="sweep-label">
              <span class="sweep-label-icon" aria-hidden="true">{{ sweep.id }}</span>
              Sweep {{ sweep.id }}: {{ sweep.name }}
            </div>
            <div class="sweep-models">
              <ModelRunNode
                v-for="run in sweep.runs"
                :key="run.id"
                :run="run"
                :active="activeModelNodes.has(run.id)"
                @hover="handleModelNodeHover"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.lineage-graph {
  position: relative;
  min-height: 500px;
  width: 100%;
}

/* SVG Connections */
.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.connection-line {
  stroke: var(--border);
  stroke-width: 2;
  fill: none;
  opacity: 0.6;
  transition: all 0.2s;
}

.connection-line.active {
  stroke: var(--accent-purple);
  stroke-width: 3;
  opacity: 1;
}

.connection-line.best {
  stroke: var(--accent-green);
  stroke-width: 3;
  opacity: 1;
}

/* Graph Layout */
.graph {
  display: flex;
  justify-content: space-between;
  position: relative;
  min-height: 500px;
  gap: 64px;
  z-index: 2;
}

.branch {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.branch-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 32px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nodes {
  display: flex;
  flex-direction: column;
  gap: 48px;
  width: 100%;
  max-width: 400px;
}

/* Sweep Cluster */
.sweep-cluster {
  background: rgba(255, 255, 255, 0.02);
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 20px;
}

.sweep-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.sweep-label-icon {
  width: 20px;
  height: 20px;
  background: var(--bg-panel);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  font-size: 11px;
  color: var(--accent-purple);
  font-weight: 700;
  border: 1px solid var(--border);
}

.sweep-models {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
