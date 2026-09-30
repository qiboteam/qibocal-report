<template>
  <footer v-if="canManageQibocal" class="admin-footer no-print" :class="{ resizing }" :style="{ height: `${displayedHeight}px` }" aria-label="Administrator diagnostics">
    <div
      class="footer-handle"
      role="separator"
      aria-orientation="horizontal"
      aria-controls="admin-diagnostics-panel"
      aria-label="Drag to resize administrator diagnostics"
      :aria-valuenow="displayedHeight"
      :aria-valuemin="8"
      :aria-valuemax="maximumHeight"
      title="Drag up to open diagnostics; drag down to collapse"
      @pointerdown="startResize"
      @pointermove="resize"
      @pointerup="finishResize"
      @pointercancel="finishResize"
      @lostpointercapture="finishResize"
    ><span /></div>
    <div v-show="diagnostics.expanded" id="admin-diagnostics-panel" class="footer-panel">
      <div class="footer-toolbar">
        <div role="tablist" aria-label="Diagnostics panels" class="footer-tabs">
          <button v-for="tab in tabs" :id="`diagnostics-tab-${tab.id}`" :key="tab.id" type="button" role="tab" :aria-selected="diagnostics.tab === tab.id" :aria-controls="`diagnostics-panel-${tab.id}`" :tabindex="diagnostics.tab === tab.id ? 0 : -1" :class="{ selected: diagnostics.tab === tab.id }" @click="diagnostics.tab = tab.id" @keydown="switchTab($event, tab.id)">{{ tab.label }}<span v-if="tab.id === 'qibocal' && diagnostics.installing" class="install-indicator" aria-label="Installation in progress" /></button>
        </div>
        <span class="footer-server">{{ state.activeServer?.name || state.activeServer?.url || 'Local Instance' }}</span>
      </div>
      <div v-show="diagnostics.tab === 'logs'" id="diagnostics-panel-logs" role="tabpanel" aria-labelledby="diagnostics-tab-logs" class="logs-panel">
        <p v-if="logError" role="alert" class="log-error">{{ logError }}</p>
        <ansi-output :text="logText" :active="diagnostics.expanded && diagnostics.tab === 'logs'" label="Server logs" placeholder="Waiting for server logs..." />
      </div>
      <div v-show="diagnostics.tab === 'qibocal'" id="diagnostics-panel-qibocal" role="tabpanel" aria-labelledby="diagnostics-tab-qibocal" class="logs-panel">
        <qibocal-panel />
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { state, canManageQibocal } from '../../store.js'
import { diagnostics } from '../../composables/useDiagnostics.js'
import { apiGetServerLogs } from '../../api.js'
import AnsiOutput from './AnsiOutput.vue'
import QibocalPanel from './QibocalPanel.vue'

const emit = defineEmits(['height'])
const tabs = [{ id: 'logs', label: 'Server logs' }, { id: 'qibocal', label: 'Qibocal' }]
const height = ref(8)
const maximumHeight = ref(600)
const displayedHeight = computed(() => diagnostics.expanded ? height.value : 8)
const resizing = ref(false)
let dragOrigin = null
const entries = ref([])
const logText = computed(() => entries.value.map(entry => entry.text).join(''))
const logError = ref('')
let cursor = 0
let timer
let controller
let pollVersion = 0

function stopPolling() {
  pollVersion++
  clearTimeout(timer)
  controller?.abort()
}

async function pollLogs(version) {
  const server = state.activeServer
  controller = new AbortController()
  try {
    const response = await apiGetServerLogs(cursor, server, controller.signal)
    const data = await response.json()
    if (version !== pollVersion) return
    if (response.status === 401 || response.status === 403) {
      entries.value = []
      logError.value = data.detail || 'Administrator access is required to read server logs.'
      return
    }
    if (!response.ok) throw new Error(data.detail || `Could not read server logs (${response.status})`)
    if (!Array.isArray(data.entries) || !Number.isInteger(data.cursor) ||
        !data.entries.every(entry => Number.isInteger(entry.id) && typeof entry.text === 'string')) {
      throw new Error('The server returned an invalid log response.')
    }
    if (data.cursor < cursor) entries.value = []
    const recent = [...entries.value, ...data.entries].slice(-2000)
    let size = 0
    let start = recent.length
    while (start > 0 && size + recent[start - 1].text.length <= 500_000) size += recent[--start].text.length
    entries.value = recent.slice(start)
    cursor = data.cursor
    logError.value = ''
  } catch (error) {
    if (version !== pollVersion || error.name === 'AbortError') return
    logError.value = error.message
  }
  if (version === pollVersion) timer = setTimeout(() => pollLogs(version), 1500)
}

watch(
  [
    () => state.activeServer?.id,
    () => state.activeServer?.url,
    () => state.auth.token,
    () => state.auth.user?.id,
    () => state.auth.user?.role,
    canManageQibocal
  ],
  () => {
    stopPolling()
    diagnostics.expanded = false
    height.value = 8
    dragOrigin = null
    resizing.value = false
    diagnostics.tab = 'logs'
    diagnostics.installing = false
    entries.value = []
    cursor = 0
    logError.value = ''
  },
  { flush: 'sync' }
)

watch(
  () => [diagnostics.expanded, diagnostics.tab, canManageQibocal.value],
  () => {
    stopPolling()
    if (canManageQibocal.value && diagnostics.expanded && diagnostics.tab === 'logs') pollLogs(pollVersion)
  }
)

watch(
  () => [diagnostics.expanded, height.value, canManageQibocal.value],
  () => {
    emit('height', canManageQibocal.value ? displayedHeight.value : 0)
    if (typeof window !== 'undefined') nextTick(() => window.dispatchEvent(new Event('resize')))
  },
  { immediate: true }
)

function switchTab(event, id) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const index = tabs.findIndex(tab => tab.id === id)
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length
  diagnostics.tab = tabs[next].id
  document.getElementById(`diagnostics-tab-${tabs[next].id}`)?.focus()
}

function updateMaximumHeight() {
  maximumHeight.value = Math.max(80, Math.floor(window.innerHeight * 0.8))
  height.value = Math.min(height.value, maximumHeight.value)
}

function startResize(event) {
  if (event.button !== 0 || event.isPrimary === false) return
  event.preventDefault()
  dragOrigin = { y: event.clientY, height: displayedHeight.value, pointerId: event.pointerId }
  resizing.value = true
  event.currentTarget.setPointerCapture(event.pointerId)
}

function resize(event) {
  if (!dragOrigin || event.pointerId !== dragOrigin.pointerId) return
  height.value = Math.max(8, Math.min(maximumHeight.value, dragOrigin.height + dragOrigin.y - event.clientY))
  diagnostics.expanded = height.value > 8
}

function finishResize(event) {
  if (!dragOrigin || event.pointerId !== dragOrigin.pointerId) return
  dragOrigin = null
  resizing.value = false
  if (height.value < 80) {
    height.value = 8
    diagnostics.expanded = false
  } else {
    height.value = Math.max(Math.min(180, maximumHeight.value), height.value)
    diagnostics.expanded = true
  }
  if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId)
}

onMounted(() => {
  updateMaximumHeight()
  window.addEventListener('resize', updateMaximumHeight)
})
onUnmounted(() => {
  stopPolling()
  window.removeEventListener('resize', updateMaximumHeight)
})
</script>

<style scoped>
.admin-footer { position: fixed; bottom: 0; left: 0; right: 0; z-index: 45; display: flex; flex-direction: column; background: #252526; color: #ddd; }
.footer-handle { height: 8px; min-height: 8px; width: 100%; display: flex; justify-content: center; align-items: center; background: #e5e7eb; cursor: ns-resize; touch-action: none; user-select: none; border-top: 1px solid #d1d5db; }
.footer-handle:hover, .resizing .footer-handle { background: #dfe0e3; }
.resizing { user-select: none; }
.footer-handle span { height: 2px; width: 44px; border-radius: 2px; background: #833dff; }
.footer-handle:hover span, .resizing .footer-handle span { background: #a878ff; }
.footer-panel { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.footer-toolbar { display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #444; min-height: 38px; padding-right: 12px; }
.footer-tabs { display: flex; align-self: stretch; }
.footer-tabs button { padding: 0 14px; font-size: 12px; color: #aaa; cursor: pointer; border-bottom: 2px solid transparent; }
.footer-tabs button.selected { color: #fff; border-color: #a878ff; }
.footer-server { flex: 1; min-width: 0; text-align: right; font-size: 11px; color: #aaa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.logs-panel { display: flex; flex: 1; min-height: 0; }
.logs-panel:has(.log-error) { flex-direction: column; }
.log-error { padding: 8px 12px; margin: 0; color: #f48771; font-size: 12px; }
.install-indicator { display: inline-block; width: 6px; height: 6px; margin-left: 7px; border-radius: 50%; background: #e5c07b; }
@media (max-width: 480px) { .footer-server { display: none; } }
</style>
