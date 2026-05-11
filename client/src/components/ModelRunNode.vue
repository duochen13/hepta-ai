<script setup>
import { computed } from 'vue'

const props = defineProps({
  run: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['hover', 'click'])

// Format timestamp
const formattedTimestamp = computed(() => {
  const date = new Date(props.run.timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
})

// Generate ARIA label
const ariaLabel = computed(() => {
  const metrics = Object.entries(props.run.metrics)
    .map(([key, val]) => {
      const quality = val.quality !== 'neutral' ? ` ${val.quality}` : ''
      return `${key} ${val.value}${quality}`
    })
    .join(', ')

  let prefix = ''
  if (props.run.best) prefix = 'Overall best model, '
  else if (props.run.sweepWinner) prefix = `Sweep ${props.run.sweep.id} winner, `
  else prefix = 'Model run '

  return `${prefix}${props.run.id}: ${props.run.message}, ${metrics}, created ${formattedTimestamp.value}`
})
</script>

<template>
  <article
    class="model-node"
    :class="{
      active,
      best: run.best,
      'sweep-winner': run.sweepWinner,
    }"
    :data-id="run.id"
    tabindex="0"
    role="button"
    :aria-label="ariaLabel"
    @mouseenter="emit('hover', run.id, true)"
    @mouseleave="emit('hover', run.id, false)"
    @click="emit('click', run.id)"
    @keypress.enter="emit('click', run.id)"
    @keypress.space.prevent="emit('click', run.id)"
  >
    <span v-if="run.best" class="best-badge">BEST</span>
    <span v-else-if="run.sweepWinner" class="sweep-winner-badge">Sweep {{ run.sweep.id }} Winner</span>

    <div class="node-header">
      <span class="node-id">{{ run.id }}</span>
      <span class="node-timestamp">{{ formattedTimestamp }}</span>
    </div>

    <div class="node-message">{{ run.message }}</div>

    <div v-if="run.metrics" class="metrics">
      <div v-for="(metric, key) in run.metrics" :key="key" class="metric">
        <div class="metric-label">{{ key }}</div>
        <div class="metric-value" :class="metric.quality">
          {{ metric.value }}
          <span v-if="metric.quality === 'good'" class="sr-only">(excellent)</span>
          <span v-else-if="metric.quality === 'ok'" class="sr-only">(good)</span>
          <span v-else-if="metric.quality === 'bad'" class="sr-only">(poor)</span>
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped>
/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.model-node {
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.model-node:hover,
.model-node:focus {
  border-color: var(--accent-green);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.model-node:focus-visible {
  outline: 2px solid var(--accent-green);
  outline-offset: 2px;
}

.model-node.active {
  border-color: var(--accent-green);
  background: rgba(16, 185, 129, 0.05);
}

.model-node.best {
  border-color: var(--accent-green);
  border-width: 3px;
}

.model-node.sweep-winner {
  border-color: var(--accent-orange);
  background: rgba(245, 158, 11, 0.05);
}

.best-badge {
  position: absolute;
  top: -10px;
  right: 12px;
  background: var(--accent-green);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
}

.sweep-winner-badge {
  position: absolute;
  top: -10px;
  right: 12px;
  background: var(--accent-orange);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.node-id {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.node-timestamp {
  font-size: 11px;
  color: var(--text-tertiary);
}

.node-message {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.metric {
  background: rgba(255, 255, 255, 0.02);
  padding: 8px;
  border-radius: 4px;
  border: 1px solid var(--border);
}

.metric-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 2px;
  font-family: var(--font-mono);
}

.metric-value.good {
  color: var(--accent-green);
}

.metric-value.ok {
  color: var(--accent-orange);
}

.metric-value.bad {
  color: var(--accent-red);
}
</style>
