<script setup>
import { computed } from 'vue'

const props = defineProps({
  commit: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['hover', 'click'])

// Format row count (1200000 → 1.2M)
const formattedRowCount = computed(() => {
  const count = props.commit.rowCount
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`
  }
  return String(count)
})

// Format timestamp
const formattedTimestamp = computed(() => {
  const date = new Date(props.commit.timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
})
</script>

<template>
  <article
    class="data-node"
    :class="{ active }"
    :data-id="commit.id"
    tabindex="0"
    role="button"
    :aria-label="`Data commit ${commit.id}: ${commit.message}, hash ${commit.hash}, ${formattedRowCount} rows, created ${formattedTimestamp}`"
    @mouseenter="emit('hover', commit.id, true)"
    @mouseleave="emit('hover', commit.id, false)"
    @click="emit('click', commit.id)"
    @keypress.enter="emit('click', commit.id)"
    @keypress.space.prevent="emit('click', commit.id)"
  >
    <div class="node-header">
      <span class="node-id">{{ commit.id }}</span>
      <span class="node-timestamp">{{ formattedTimestamp }}</span>
    </div>
    <div class="node-message">{{ commit.message }}</div>
    <div class="node-meta">hash: {{ commit.hash }} • {{ formattedRowCount }} rows</div>
  </article>
</template>

<style scoped>
.data-node {
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.data-node:hover,
.data-node:focus {
  border-color: var(--accent-purple);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.data-node:focus-visible {
  outline: 2px solid var(--accent-purple);
  outline-offset: 2px;
}

.data-node.active {
  border-color: var(--accent-purple);
  background: rgba(139, 92, 246, 0.05);
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

.node-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
}
</style>
