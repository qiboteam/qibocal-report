import { ref, computed, watch, onUnmounted } from 'vue'
import { apiFetch } from '../api.js'
import { state, canEdit, isAdmin, getActiveAuthToken } from '../store.js'

export function normalizeNotes(notes) {
  return Array.isArray(notes)
    ? notes.filter(note => note && typeof note.content === 'string')
    : []
}

/**
 * The comments of a report, or of one of its protocols: read when the panel
 * opens, added, changed and removed through the server, which keeps the
 * history in Qibocal's own notes.json. A comment is addressed by its position
 * and its timestamp, so a stale history cannot touch the wrong one: the
 * server answers 409, and the history is reloaded.
 */
export function useNotes(props, emit) {
  const notes = ref(normalizeNotes(props.notes))
  const draft = ref('')
  const expanded = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  /** The comment being changed in place, by position, and its new text. */
  const editing = ref(null)
  const editDraft = ref('')
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

  /** Whoever wrote a comment may change it; an administrator any; on an open server, anyone. */
  const canChange = note => {
    if (!canEdit.value) return false
    if (!state.auth?.enabled || isAdmin.value) return true
    return Boolean(note?.author) && note.author === state.auth?.user?.username
  }
  const changeable = computed(() => notes.value.some(canChange))

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
    editing.value = null
    error.value = ''
    loading.value = false
    saving.value = false
    if (expanded.value) loadNotes()
  }, { flush: 'sync' })

  async function responseNotes(response) {
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      const failure = new Error(typeof body?.detail === 'string'
        ? body.detail
        : `Notes request failed (${response.status})`)
      failure.status = response.status
      throw failure
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

  /**
   * Send a change — an addition, a replacement, a removal — and take the
   * history the server answers with, unless a newer one arrived meanwhile,
   * in which case it is reloaded. A 409 — the comments changed under us —
   * reloads too, and says so.
   */
  async function change(request, failure, after = () => {}) {
    const context = contextVersion
    const revision = historyVersion
    const server = captureServer()
    let refresh = false
    readVersion++
    loading.value = false
    saving.value = true
    error.value = ''
    try {
      const history = await responseNotes(await apiFetch(request.path, request.options, server))
      if (context !== contextVersion) return
      after()
      if (revision !== historyVersion) {
        refresh = true
      } else {
        notes.value = history
        emit('update:notes', history)
      }
    } catch (err) {
      if (context !== contextVersion) return
      error.value = err.message || failure
      if (err.status === 409) refresh = true
    } finally {
      if (context === contextVersion) {
        saving.value = false
        if (refresh) await loadNotes()
      }
    }
  }

  async function addComment() {
    if (!canEdit.value || saving.value || !props.reportId || !draft.value.trim()) return
    const content = draft.value
    await change({
      path: path(),
      options: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      }
    }, 'Unable to add comment', () => {
      if (draft.value === content) draft.value = ''
    })
  }

  function startEdit(index) {
    if (!canChange(notes.value[index]) || saving.value) return
    editing.value = index
    editDraft.value = notes.value[index].content
  }

  function cancelEdit() {
    editing.value = null
    editDraft.value = ''
  }

  async function saveEdit() {
    const index = editing.value
    const note = notes.value[index]
    if (index === null || !note || saving.value || !editDraft.value.trim()) return
    const content = editDraft.value
    await change({
      path: `${path()}/${index}`,
      options: {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, timestamp: note.timestamp })
      }
    }, 'Unable to change the comment', cancelEdit)
  }

  async function removeComment(index) {
    const note = notes.value[index]
    if (!note || !canChange(note) || saving.value) return
    if (editing.value === index) cancelEdit()
    await change({
      path: `${path()}/${index}?timestamp=${encodeURIComponent(note.timestamp)}`,
      options: { method: 'DELETE' }
    }, 'Unable to remove the comment')
  }

  function toggle(open) {
    expanded.value = open
    if (open) loadNotes()
  }

  onUnmounted(() => {
    contextVersion++
    readVersion++
  })

  return {
    notes, draft, expanded, loading, saving, error,
    editing, editDraft, changeable, canChange,
    loadNotes, addComment, startEdit, cancelEdit, saveEdit, removeComment, toggle
  }
}
