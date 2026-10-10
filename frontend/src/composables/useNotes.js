import { ref, watch, onUnmounted } from 'vue'
import { apiFetch } from '../api.js'
import { state, canEdit, getActiveAuthToken } from '../store.js'

export function normalizeNotes(notes) {
  return Array.isArray(notes)
    ? notes.filter(note => note && typeof note.content === 'string')
    : []
}

export function useNotes(props, emit) {
  const notes = ref(normalizeNotes(props.notes))
  const draft = ref('')
  const expanded = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  let contextVersion = 0
  let readVersion = 0
  let historyVersion = 0

  const path = () => {
    const report = `/api/reports/${encodeURIComponent(props.reportId)}`
    return props.protocolId == null
      ? `${report}/notes`
      : `${report}/protocols/${encodeURIComponent(props.protocolId)}/notes`
  }
  const captureServer = () => state.activeServer ? { ...state.activeServer } : null

  watch(() => props.notes, value => {
    notes.value = normalizeNotes(value)
    // New streamed or regenerated histories supersede pending request histories.
    historyVersion++
    readVersion++
    loading.value = false
  }, { deep: true, flush: 'sync' })

  watch(() => [
    props.reportId, props.protocolId,
    state.activeServer?.id, state.activeServer?.url,
    state.auth.enabled, state.auth.token,
    state.auth.user?.id, state.auth.user?.username, state.auth.user?.role,
    getActiveAuthToken()
  ], () => {
    contextVersion++
    readVersion++
    notes.value = []
    draft.value = ''
    error.value = ''
    loading.value = false
    saving.value = false
    if (expanded.value) loadNotes()
  }, { flush: 'sync' })

  async function responseNotes(response) {
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      throw new Error(typeof body?.detail === 'string'
        ? body.detail
        : `Notes request failed (${response.status})`)
    }
    const history = await response.json()
    if (!Array.isArray(history) || history.some(note =>
      !note || typeof note.content !== 'string' || typeof note.timestamp !== 'string' ||
      (note.author != null && typeof note.author !== 'string')
    )) throw new Error('Invalid notes history returned by server')
    return history
  }

  async function loadNotes() {
    if (!props.reportId || saving.value) return
    const context = contextVersion
    const request = ++readVersion
    const server = captureServer()
    loading.value = true
    error.value = ''
    const current = () => context === contextVersion && request === readVersion
    try {
      const history = await responseNotes(await apiFetch(path(), { cache: 'no-store' }, server))
      if (!current()) return
      notes.value = history
      emit('update:notes', history)
    } catch (err) {
      if (current()) error.value = err.message || 'Unable to load comments'
    } finally {
      if (current()) loading.value = false
    }
  }

  async function addComment() {
    if (!canEdit.value || saving.value || !props.reportId || !draft.value.trim()) return
    const context = contextVersion
    const revision = historyVersion
    const server = captureServer()
    const content = draft.value
    let refresh = false
    readVersion++
    loading.value = false
    saving.value = true
    error.value = ''
    try {
      const history = await responseNotes(await apiFetch(path(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      }, server))
      if (context !== contextVersion) return
      if (draft.value === content) draft.value = ''
      if (revision !== historyVersion) {
        refresh = true
      } else {
        notes.value = history
        emit('update:notes', history)
      }
    } catch (err) {
      if (context === contextVersion) error.value = err.message || 'Unable to add comment'
    } finally {
      if (context === contextVersion) {
        saving.value = false
        if (refresh) await loadNotes()
      }
    }
  }

  function toggle(open) {
    expanded.value = open
    if (open) loadNotes()
  }

  onUnmounted(() => {
    contextVersion++
    readVersion++
  })

  return { notes, draft, expanded, loading, saving, error, loadNotes, addComment, toggle }
}
