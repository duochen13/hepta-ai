<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import ChatPanel from './components/ChatPanel.vue'

const route = useRoute()

// Chatbox toggle state
const STORAGE_KEY = 'datavint_chatbox_collapsed'
const chatboxCollapsed = ref(false)

// Breadcrumb based on route
const breadcrumb = computed(() => {
  if (route.params.experimentId) {
    return `experiments > ${route.params.experimentId}`
  }
  return 'experiments'
})

function toggleChatbox() {
  chatboxCollapsed.value = !chatboxCollapsed.value
  try {
    localStorage.setItem(STORAGE_KEY, String(chatboxCollapsed.value))
  } catch (e) {
    console.warn('localStorage unavailable:', e)
  }
}

function loadCollapseState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved !== null) {
      chatboxCollapsed.value = saved === 'true'
    } else if (window.innerWidth < 768) {
      chatboxCollapsed.value = true
    }
  } catch (e) {
    console.warn('localStorage unavailable:', e)
  }
}

function handleKeyboard(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault()
    toggleChatbox()
  }
}

onMounted(() => {
  loadCollapseState()
  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="header" role="banner">
      <!-- Hamburger Toggle -->
      <button
        class="hamburger-toggle"
        @click="toggleChatbox"
        :title="chatboxCollapsed ? 'Show Assistant (Ctrl+B)' : 'Hide Assistant (Ctrl+B)'"
        :aria-label="chatboxCollapsed ? 'Show assistant sidebar' : 'Hide assistant sidebar'"
        :aria-expanded="!chatboxCollapsed"
      >
        <div class="hamburger-icon">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </button>

      <!-- Logo -->
      <div class="logo">
        <div class="logo-icon" aria-hidden="true"></div>
        DataVint
      </div>

      <!-- Breadcrumb -->
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <span class="breadcrumb-item">{{ breadcrumb }}</span>
      </nav>
    </header>

    <!-- Main Content: Split Panel -->
    <div class="content-wrapper">
      <!-- Chat Panel (Left Sidebar) -->
      <aside
        v-show="!chatboxCollapsed"
        class="chat-sidebar"
        :class="{ collapsed: chatboxCollapsed }"
        role="complementary"
        aria-label="Chat assistant"
      >
        <ChatPanel />
      </aside>

      <!-- Main Content Area -->
      <main class="main-content" :class="{ 'full-width': chatboxCollapsed }" role="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.header {
  background: var(--bg-panel);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  height: 57px;
  position: relative;
  padding: 0 24px;
  gap: 24px;
}

/* Hamburger Toggle */
.hamburger-toggle {
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  flex-shrink: 0;
}

.hamburger-toggle:hover,
.hamburger-toggle:focus {
  background: var(--bg-hover);
  outline: none;
}

.hamburger-toggle:focus-visible {
  outline: 2px solid var(--accent-cyan);
  outline-offset: 2px;
}

.hamburger-icon {
  width: 20px;
  height: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
}

.hamburger-icon span {
  display: block;
  height: 2px;
  background: var(--text-secondary);
  border-radius: 2px;
  transition: all 0.2s ease;
}

.hamburger-toggle:hover .hamburger-icon span {
  background: var(--accent-cyan);
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  flex-shrink: 0;
}

.logo-icon {
  width: 8px;
  height: 8px;
  background: var(--accent-purple);
  border-radius: 2px;
}

/* Breadcrumb */
.breadcrumb {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.breadcrumb-item {
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Content Wrapper: Split Panel */
.content-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Chat Sidebar */
.chat-sidebar {
  width: 380px;
  min-width: 280px;
  max-width: 400px;
  border-right: 1px solid var(--border);
  transition: transform 0.3s ease, opacity 0.3s ease;
  transform: translateX(0);
  opacity: 1;
  background: var(--bg-panel);
  flex-shrink: 0;
}

.chat-sidebar.collapsed {
  transform: translateX(-100%);
  opacity: 0;
  pointer-events: none;
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: hidden;
  transition: margin-left 0.3s ease;
  min-width: 0;
}

.main-content.full-width {
  margin-left: 0;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    width: 80%;
    max-width: none;
    box-shadow: var(--shadow-lg);
  }

  .logo {
    font-size: 14px;
  }

  .breadcrumb {
    font-size: 12px;
  }
}
</style>
