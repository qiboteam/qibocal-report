import { ref, watch, onUnmounted } from 'vue'
import { state, addToHistory, removeFromHistory, getActiveWsUrl, canEdit } from '../store.js'
import { REPORT_FIELDS, apiFetch, apiGraphQL } from '../api.js'
import { getPlotGenerationErrors } from '../utils/plotGeneration.js'
import { announce } from '../utils/desktop.js'
import { createLiveReportSubscription, mergeLiveProtocols, synchronizeLiveProtocols } from '../utils/liveReport.js'

/**
 * Sort protocol objects by execution order using history or stats from report detail.
 */
export function sortProtocolsByExecutionOrder(protocolsList, reportDetail) {
  if (!protocolsList || protocolsList.length <= 1) return protocolsList || []
  const history = reportDetail?.history
  const stats = reportDetail?.meta?.stats || reportDetail?.stats

  let order = []
  if (Array.isArray(history) && history.length > 0) {
    order = history
      .map(item => (typeof item === 'string' ? item : item?.id || item?.task || item?.name))
      .filter(Boolean)
  } else if (history && typeof history === 'object' && Object.keys(history).length > 0) {
    order = Object.keys(history)
  } else if (stats && typeof stats === 'object' && Object.keys(stats).length > 0) {
    order = Object.keys(stats)
  } else if (Array.isArray(reportDetail?.protocols_summary) && reportDetail.protocols_summary.length > 0) {
    order = reportDetail.protocols_summary.map(p => p.id).filter(Boolean)
  }

  if (order.length === 0) return protocolsList

  const norm = s => String(s || '').toLowerCase().replace(/[-_]/g, '').trim()
  const base = s => {
    const n = String(s || '').toLowerCase().replace(/-/g, '_').trim()
    const lastIdx = n.lastIndexOf('_')
    if (lastIdx !== -1 && /^\d+$/.test(n.slice(lastIdx + 1))) {
      return n.slice(0, lastIdx).replace(/_/g, '')
    }
    return n.replace(/_/g, '')
  }

  const usedSlots = new Set()
  const assignedSlots = new Map()

  // Pass 1: exact matches
  protocolsList.forEach((p, idx) => {
    const pid = String(p.id || '')
    for (let i = 0; i < order.length; i++) {
      if (!usedSlots.has(i) && pid === order[i]) {
        usedSlots.add(i)
        assignedSlots.set(idx, i)
        break
      }
    }
  })

  // Pass 2: normalized matches
  protocolsList.forEach((p, idx) => {
    if (assignedSlots.has(idx)) return
    const pidNorm = norm(p.id)
    for (let i = 0; i < order.length; i++) {
      if (!usedSlots.has(i) && pidNorm === norm(order[i])) {
        usedSlots.add(i)
        assignedSlots.set(idx, i)
        break
      }
    }
  })

  // Pass 3: base key matches
  protocolsList.forEach((p, idx) => {
    if (assignedSlots.has(idx)) return
    const pidBase = base(p.id)
    for (let i = 0; i < order.length; i++) {
      if (!usedSlots.has(i) && pidBase === base(order[i])) {
        usedSlots.add(i)
        assignedSlots.set(idx, i)
        break
      }
    }
  })

  return [...protocolsList].sort((a, b) => {
    const idxA = protocolsList.indexOf(a)
    const idxB = protocolsList.indexOf(b)
    const slotA = assignedSlots.has(idxA) ? assignedSlots.get(idxA) : order.length
    const slotB = assignedSlots.has(idxB) ? assignedSlots.get(idxB) : order.length
    if (slotA !== slotB) return slotA - slotB
    return idxA - idxB
  })
}

/**
 * Composable for loading report details via WebSocket streaming or HTTP fallback,
 * managing routine protocols, plot regeneration, author updates, and tag removals.
 */
/**
 * The report, with its protocols named but their outputs left out: what the
 * cards need to exist. The HTML and the figures of each come separately,
 * one protocol at a time, as its card nears the viewport.
 */
const REPORT_QUERY = `
  query Report($id: String!) {
    report(id: $id) {
      ${REPORT_FIELDS}
      history
      protocols_summary { id name category execution_time status num_figures }
      notes { content timestamp author }
      protocols_detail {
        id name category execution_time status num_figures
        notes { content timestamp author }
      }
    }
  }
`
const OUTPUTS_QUERY = `
  query Outputs($report_id: String!, $protocol_id: String!) {
    protocol(report_id: $report_id, protocol_id: $protocol_id) { html figures error error_code }
  }
`
/** How many protocols' outputs are in flight at once. */
const OUTPUTS_CONCURRENCY = 2

export function useReportDetail(reportId) {
  const loading = ref(true)
  const loadingStatus = ref('Connecting to server...')
  const error = ref(null)
  const report = ref(null)
  const protocols = ref([])
  const regenerating = ref(false)
  const statusBanner = ref('')
  const statusBannerError = ref(false)
  const savingAuthor = ref(false)
  const live = ref(false)
  const liveConnecting = ref(false)

  let activeWs = null
  const liveSubscription = createLiveReportSubscription({
    onState(value) {
      live.value = value === 'active'
      liveConnecting.value = value === 'connecting'
    },
    onError(message) {
      showBanner(message, 0, true)
    },
    onMessage(message) {
      if (message.type === 'metadata') {
        report.value = message.report
        addToHistory(message.report)
        protocols.value = sortProtocolsByExecutionOrder(protocols.value, message.report)
      } else if (message.type === 'snapshot') {
        protocols.value = sortProtocolsByExecutionOrder(
          synchronizeLiveProtocols(protocols.value, message.protocols),
          report.value
        )
      } else if (message.type === 'update') {
        protocols.value = sortProtocolsByExecutionOrder(
          mergeLiveProtocols(protocols.value, message.protocols, message.removed),
          report.value
        )
        const errors = getPlotGenerationErrors(message.protocols)
        if (errors.length) showBanner(`Live plot errors: ${errors.join(' ')}`, 0, true)
      }
    }
  })

  function toggleLive() {
    if (live.value || liveConnecting.value) {
      liveSubscription.stop()
    } else if (canEdit.value && !loading.value && !regenerating.value && report.value) {
      statusBanner.value = ''
      liveSubscription.start(getActiveWsUrl(
        `/ws/live/reports/${encodeURIComponent(report.value.id)}`
      ))
    }
  }

  watch(
    [
      () => typeof reportId === 'function' ? reportId() : reportId.value,
      () => state.activeServer?.id,
      () => state.activeServer?.url,
      () => state.auth.token,
      () => state.auth.user?.id,
      () => state.auth.user?.role,
      canEdit
    ],
    () => liveSubscription.stop(),
    { flush: 'sync' }
  )

  function showBanner(msg, durationMs = 3500, isError = false) {
    // Inside the launcher, the message goes where everything is said.
    if (announce(msg, isError ? 'error' : 'info')) return
    statusBanner.value = msg
    statusBannerError.value = isError
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
            if (protocols.value?.length > 0) {
              protocols.value = sortProtocolsByExecutionOrder(protocols.value, msg.report)
            }
          } else if (msg.type === 'status') {
            loadingStatus.value = msg.message
          } else if (msg.type === 'progress') {
            loadingStatus.value = msg.message || `Plotting routine (${msg.step}/${msg.total})...`
          } else if (msg.type === 'ready') {
            clearTimeout(timer)
            resolved = true
            protocols.value = sortProtocolsByExecutionOrder(msg.protocols, report.value)
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

  // --- The outputs, protocol by protocol ------------------------------------

  /** Which load the outputs belong to: a new report, or server, drops the old requests. */
  let outputsContext = 0
  const outputsQueue = { near: [], later: [], active: 0, server: null, reportId: null }

  function setProtocol(id, changes) {
    const index = protocols.value.findIndex(protocol => protocol.id === id)
    if (index < 0) return
    const next = [...protocols.value]
    next[index] = { ...next[index], ...changes }
    protocols.value = next
  }

  async function fetchOutputs(id, context) {
    setProtocol(id, { outputs: 'loading' })
    let outputs = null
    try {
      const data = await apiGraphQL(OUTPUTS_QUERY, { report_id: outputsQueue.reportId, protocol_id: id }, outputsQueue.server)
      outputs = data?.protocol || null
    } catch (err) {
      console.warn(`Outputs of ${id} could not be fetched`, err)
    }
    if (context !== outputsContext) return
    if (!outputs) {
      setProtocol(id, { outputs: 'failed' })
      return
    }
    setProtocol(id, { ...outputs, figures: outputs.figures || [], outputs: 'ready' })
  }

  function pumpOutputs(context) {
    while (outputsQueue.active < OUTPUTS_CONCURRENCY) {
      const id = outputsQueue.near.shift() ?? outputsQueue.later.shift()
      if (id === undefined) return
      const protocol = protocols.value.find(entry => entry.id === id)
      if (!protocol || protocol.outputs !== 'pending') continue
      outputsQueue.active += 1
      fetchOutputs(id, context).finally(() => {
        outputsQueue.active -= 1
        if (context !== outputsContext) return
        // The ones in view follow at once; the rest wait for an idle moment.
        if (outputsQueue.near.length) pumpOutputs(context)
        else idle(() => pumpOutputs(context))
      })
    }
  }

  function idle(callback) {
    if (typeof requestIdleCallback === 'function') requestIdleCallback(callback, { timeout: 1000 })
    else setTimeout(callback, 100)
  }

  /** A card came near: its outputs go to the head of the line. */
  function requestProtocolOutputs(id) {
    const protocol = protocols.value.find(entry => entry.id === id)
    if (!protocol || protocol.outputs !== 'pending') return
    outputsQueue.later = outputsQueue.later.filter(entry => entry !== id)
    if (!outputsQueue.near.includes(id)) outputsQueue.near.push(id)
    pumpOutputs(outputsContext)
  }

  /** Everything still pending, in reading order, for the idle moments. */
  function prefetchOutputs() {
    outputsQueue.later = protocols.value.filter(entry => entry.outputs === 'pending').map(entry => entry.id)
    idle(() => pumpOutputs(outputsContext))
  }

  /**
   * The report over GraphQL, its protocols named but not yet fetched.
   * Answers 'ready' when the outputs can be fetched one by one — a report
   * with pre-cached outputs — and 'generate' when they have to be generated
   * first, which the WebSocket does with progress. A missing report is
   * thrown.
   */
  async function loadViaGraphQL(id) {
    const data = await apiGraphQL(REPORT_QUERY, { id })
    if (!data?.report) {
      removeFromHistory(id)
      throw new Error('Report not found (404)')
    }
    const { protocols_detail: named, ...metadata } = data.report
    report.value = metadata
    state.currentReportId = metadata.id
    addToHistory(metadata)
    if (!metadata.has_cached_report) return 'generate'
    outputsContext += 1
    outputsQueue.near = []
    outputsQueue.later = []
    outputsQueue.server = state.activeServer
    outputsQueue.reportId = id
    protocols.value = sortProtocolsByExecutionOrder(
      (named || []).map(protocol => ({ ...protocol, html: '', figures: [], outputs: 'pending' })),
      metadata
    )
    return 'ready'
  }

  /** The protocols generated in one request, where the WebSocket could not be opened. */
  async function loadProtocolsViaHttp(id) {
    try {
      loadingStatus.value = 'Retrieving report protocols...'
      const protoRes = await apiFetch(`/api/reports/${encodeURIComponent(id)}/protocols`)
      if (!protoRes.ok) throw new Error(`Failed to load protocols (${protoRes.status})`)
      protocols.value = sortProtocolsByExecutionOrder(await protoRes.json(), report.value)
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function loadReportData() {
    const id = typeof reportId === 'function' ? reportId() : reportId.value
    if (!id) return
    liveSubscription.stop()

    loading.value = true
    error.value = null
    report.value = null
    protocols.value = []
    regenerating.value = false
    statusBanner.value = ''
    loadingStatus.value = 'Connecting to server...'

    if (activeWs) {
      try { activeWs.close() } catch {}
      activeWs = null
    }
    outputsContext += 1

    // One request names the report and its protocols; a pre-cached report
    // then fetches its outputs card by card. One that has to generate its
    // plots goes through the WebSocket, which reports the progress.
    try {
      loadingStatus.value = 'Fetching report...'
      const via = await loadViaGraphQL(id)
      if (via === 'ready') {
        loading.value = false
        prefetchOutputs()
        return
      }
    } catch (err) {
      error.value = err.message
      loading.value = false
      return
    }

    try {
      const wsOk = await connectWebSocket(id)
      if (wsOk) return
    } catch (err) {
      console.warn('WebSocket streaming unavailable, falling back to HTTP:', err)
    }

    await loadProtocolsViaHttp(id)
  }

  async function handleRegenerate() {
    const id = typeof reportId === 'function' ? reportId() : reportId.value
    if (!id || regenerating.value) return
    liveSubscription.stop()
    const server = state.activeServer
    const isCurrent = () => server === state.activeServer && id === (typeof reportId === 'function' ? reportId() : reportId.value)
    regenerating.value = true
    statusBanner.value = ''
    try {
      const encodedId = encodeURIComponent(id)
      const res = await apiFetch(`/api/reports/${encodedId}/regenerate`, { method: 'POST' }, server)
      if (res.ok) {
        const regenData = await res.json()
        if (!isCurrent()) return
        protocols.value = sortProtocolsByExecutionOrder(regenData, report.value)
        const generationErrors = getPlotGenerationErrors(regenData)
        if (generationErrors.length) {
          showBanner(`Some plots could not be generated: ${generationErrors.join(' ')}`, 0, true)
        } else {
          showBanner('Report plots regenerated successfully!', 3500)
        }
        if (report.value) {
          report.value.has_cached_report = regenData.some(proto => proto.status === 'success')
        }
      } else {
        const data = await res.json()
        throw new Error(data.detail || `Regeneration failed (${res.status})`)
      }
    } catch (err) {
      if (isCurrent()) alert('Regeneration failed: ' + err.message)
    } finally {
      if (isCurrent()) regenerating.value = false
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
      // In the body: a tag in the path could be `..`, which the browser collapses.
      const res = await apiFetch('/api/reports/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'unlabel', report_ids: [report.value.id], label: tag })
      })
      if (res.ok) {
        if (Array.isArray(report.value.tags)) {
          report.value.tags = report.value.tags.filter(t => t !== tag)
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
    liveSubscription.stop()
    if (activeWs) {
      try { activeWs.close() } catch {}
      activeWs = null
    }
  })

  return {
    requestProtocolOutputs,
    loading,
    loadingStatus,
    error,
    report,
    protocols,
    regenerating,
    statusBanner,
    statusBannerError,
    savingAuthor,
    live,
    liveConnecting,
    toggleLive,
    loadReportData,
    handleRegenerate,
    handleSaveAuthor,
    handleRemoveTag
  }
}
