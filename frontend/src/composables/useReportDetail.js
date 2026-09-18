import { ref, onUnmounted } from 'vue'
import { state, addToHistory, removeFromHistory, apiFetch, getActiveWsUrl } from '../store.js'

/**
 * Composable for loading report details via WebSocket streaming or HTTP fallback,
 * managing routine protocols, plot regeneration, author updates, and tag removals.
 */
export function useReportDetail(reportId) {
  const loading = ref(true)
  const loadingStatus = ref('Connecting to server...')
  const error = ref(null)
  const report = ref(null)
  const protocols = ref([])
  const regenerating = ref(false)
  const statusBanner = ref('')
  const savingAuthor = ref(false)

  let activeWs = null

  function showBanner(msg, durationMs = 3500) {
    statusBanner.value = msg
    if (durationMs > 0) {
      setTimeout(() => {
        if (statusBanner.value === msg) {
          statusBanner.value = ''
        }
      }, durationMs)
    }
  }

  function connectWebSocket(id) {
    return new Promise((resolve, reject) => {
      const encodedId = encodeURIComponent(id)
      const wsUrl = getActiveWsUrl(`/ws/reports/${encodedId}`)

      let ws = null
      try {
        ws = new WebSocket(wsUrl)
        activeWs = ws
      } catch (e) {
        reject(e)
        return
      }

      let resolved = false

      // 15-second safety timer before falling back to HTTP
      const timer = setTimeout(() => {
        if (!resolved) {
          resolved = true
          try { ws.close() } catch {}
          reject(new Error('WebSocket connection timed out'))
        }
      }, 15000)

      ws.onopen = () => {
        loadingStatus.value = 'Analyzing report directory...'
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'metadata') {
            report.value = msg.report
            state.currentReportId = msg.report.id
            addToHistory(msg.report)
          } else if (msg.type === 'status') {
            loadingStatus.value = msg.message
          } else if (msg.type === 'progress') {
            loadingStatus.value = msg.message || `Plotting routine (${msg.step}/${msg.total})...`
          } else if (msg.type === 'ready') {
            clearTimeout(timer)
            resolved = true
            protocols.value = msg.protocols
            loading.value = false
            resolve(true)
          } else if (msg.type === 'error') {
            clearTimeout(timer)
            resolved = true
            if (msg.message && msg.message.toLowerCase().includes('not found')) {
              removeFromHistory(id)
            }
            reject(new Error(msg.message || 'Report not found'))
          }
        } catch (e) {
          console.error('Failed to parse WS payload', e)
        }
      }

      ws.onerror = (e) => {
        if (!resolved) {
          clearTimeout(timer)
          resolved = true
          reject(e)
        }
      }

      ws.onclose = () => {
        if (!resolved && loading.value) {
          clearTimeout(timer)
          resolved = true
          reject(new Error('WebSocket closed before completion'))
        }
      }
    })
  }

  async function loadViaHttp(id) {
    try {
      loadingStatus.value = 'Fetching report metadata...'
      const encodedId = encodeURIComponent(id)
      const res = await apiFetch(`/api/reports/${encodedId}`)
      if (!res.ok) {
        if (res.status === 404) {
          removeFromHistory(id)
        }
        throw new Error(`Report not found (${res.status})`)
      }
      const data = await res.json()
      report.value = data
      state.currentReportId = data.id
      addToHistory(data)

      loadingStatus.value = 'Retrieving report protocols...'
      const protoRes = await apiFetch(`/api/reports/${encodedId}/protocols`)
      if (protoRes.ok) {
        protocols.value = await protoRes.json()
      } else {
        throw new Error(`Failed to load protocols (${protoRes.status})`)
      }
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function loadReportData() {
    const id = typeof reportId === 'function' ? reportId() : reportId.value
    if (!id) return

    loading.value = true
    error.value = null
    report.value = null
    protocols.value = []
    statusBanner.value = ''
    loadingStatus.value = 'Connecting to server...'

    if (activeWs) {
      try { activeWs.close() } catch {}
      activeWs = null
    }

    try {
      const wsOk = await connectWebSocket(id)
      if (wsOk) return
    } catch (err) {
      console.warn('WebSocket streaming unavailable, falling back to HTTP:', err)
    }

    await loadViaHttp(id)
  }

  async function handleRegenerate() {
    const id = typeof reportId === 'function' ? reportId() : reportId.value
    if (!id) return
    regenerating.value = true
    statusBanner.value = ''
    try {
      const encodedId = encodeURIComponent(id)
      const res = await apiFetch(`/api/reports/${encodedId}/regenerate`, { method: 'POST' })
      if (res.ok) {
        protocols.value = await res.json()
        showBanner('Report plots regenerated successfully!', 3500)
        if (report.value) {
          report.value.has_cached_report = true
        }
      } else {
        throw new Error(`Regeneration failed (${res.status})`)
      }
    } catch (err) {
      alert('Regeneration failed: ' + err.message)
    } finally {
      regenerating.value = false
    }
  }

  async function handleSaveAuthor({ author, onComplete }) {
    if (!report.value) return
    savingAuthor.value = true
    try {
      const encodedId = encodeURIComponent(report.value.id)
      const res = await apiFetch(`/api/reports/${encodedId}/author`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ author })
      })
      if (res.ok) {
        report.value.author = author || 'Unknown'
        if (onComplete) onComplete()
        showBanner('Author updated successfully!')
      } else {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to update author')
      }
    } catch (err) {
      alert('Failed to update author: ' + err.message)
    } finally {
      savingAuthor.value = false
    }
  }

  async function handleRemoveTag(tag) {
    if (!report.value || !tag) return
    try {
      const encodedId = encodeURIComponent(report.value.id)
      const encodedTag = encodeURIComponent(tag)
      const res = await apiFetch(`/api/reports/${encodedId}/label/${encodedTag}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        if (Array.isArray(report.value.tags)) {
          report.value.tags = report.value.tags.filter(t => t !== tag)
        }
        if (Array.isArray(report.value.labels)) {
          report.value.labels = report.value.labels.filter(t => t !== tag)
        }
        showBanner(`Removed tag '${tag}'`)
      } else {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to remove tag')
      }
    } catch (err) {
      alert('Failed to remove tag: ' + err.message)
    }
  }

  onUnmounted(() => {
    if (activeWs) {
      try { activeWs.close() } catch {}
      activeWs = null
    }
  })

  return {
    loading,
    loadingStatus,
    error,
    report,
    protocols,
    regenerating,
    statusBanner,
    savingAuthor,
    loadReportData,
    handleRegenerate,
    handleSaveAuthor,
    handleRemoveTag
  }
}
