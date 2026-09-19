import { ref } from 'vue'
import { apiFetch, removeFromHistory } from '../store.js'

/**
 * Composable for managing report selection and bulk actions (labeling, author change, deletion).
 */
export function useBulkActions() {
  const selectedReports = ref([])
  const bulkActionInProgress = ref(false)
  const bulkError = ref(null)
  const bulkSuccessMessage = ref('')

  // Modals visibility state
  const showLabelModal = ref(false)
  const showUnlabelModal = ref(false)
  const showAuthorModal = ref(false)
  const showArchiveModal = ref(false)
  const showDeleteModal = ref(false)

  // Context for single-item vs bulk author editing
  const targetReportIdForAuthor = ref(null)
  const authorInitialValue = ref('')

  function toggleSelect(id) {
    const idx = selectedReports.value.indexOf(id)
    if (idx >= 0) {
      selectedReports.value.splice(idx, 1)
    } else {
      selectedReports.value.push(id)
    }
  }

  function toggleSelectAll(currentIds = []) {
    const allSelected =
      currentIds.length > 0 && currentIds.every(id => selectedReports.value.includes(id))
    if (allSelected) {
      selectedReports.value = selectedReports.value.filter(id => !currentIds.includes(id))
    } else {
      selectedReports.value = Array.from(new Set([...selectedReports.value, ...currentIds]))
    }
  }

  function clearSelection() {
    selectedReports.value = []
  }

  function openLabelModal() {
    bulkError.value = null
    showLabelModal.value = true
  }

  function openUnlabelModal() {
    bulkError.value = null
    showUnlabelModal.value = true
  }

  function openAuthorModal(targetReport = null) {
    bulkError.value = null
    if (targetReport?.id) {
      targetReportIdForAuthor.value = targetReport.id
      authorInitialValue.value = targetReport.author === 'Unknown' ? '' : (targetReport.author || '')
    } else {
      targetReportIdForAuthor.value = null
      authorInitialValue.value = ''
    }
    showAuthorModal.value = true
  }

  function openArchiveModal() {
    bulkError.value = null
    showArchiveModal.value = true
  }

  function openDeleteModal() {
    bulkError.value = null
    showDeleteModal.value = true
  }

  function showSuccess(msg, timeoutMs = 4000) {
    bulkSuccessMessage.value = msg
    if (timeoutMs > 0) {
      setTimeout(() => {
        if (bulkSuccessMessage.value === msg) {
          bulkSuccessMessage.value = ''
        }
      }, timeoutMs)
    }
  }

  async function applyBulkLabel(labelText, onSuccess) {
    const label = labelText.trim()
    if (!label || selectedReports.value.length === 0) return
    bulkActionInProgress.value = true
    bulkError.value = null
    try {
      const res = await apiFetch('/api/reports/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'label',
          report_ids: selectedReports.value,
          label
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to apply label')
      }
      const data = await res.json()
      showLabelModal.value = false
      selectedReports.value = []
      showSuccess(data.message || 'Label applied successfully')
      if (onSuccess) await onSuccess()
    } catch (err) {
      bulkError.value = err.message
    } finally {
      bulkActionInProgress.value = false
    }
  }

  async function applyBulkUnlabel(labelText, onSuccess) {
    const label = labelText.trim()
    if (!label || selectedReports.value.length === 0) return
    bulkActionInProgress.value = true
    bulkError.value = null
    try {
      const res = await apiFetch('/api/reports/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'unlabel',
          report_ids: selectedReports.value,
          label
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to remove label')
      }
      const data = await res.json()
      showUnlabelModal.value = false
      selectedReports.value = []
      showSuccess(data.message || 'Label removed successfully')
      if (onSuccess) await onSuccess()
    } catch (err) {
      bulkError.value = err.message
    } finally {
      bulkActionInProgress.value = false
    }
  }

  async function applyAuthor(authorText, onSuccess) {
    const authorVal = (authorText || '').trim()
    const reportIds = targetReportIdForAuthor.value
      ? [targetReportIdForAuthor.value]
      : selectedReports.value
    if (reportIds.length === 0) return
    bulkActionInProgress.value = true
    bulkError.value = null
    try {
      const res = await apiFetch('/api/reports/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'author',
          report_ids: reportIds,
          author: authorVal
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to update author')
      }
      const data = await res.json()
      showAuthorModal.value = false
      targetReportIdForAuthor.value = null
      authorInitialValue.value = ''
      selectedReports.value = []
      showSuccess(data.message || 'Author updated successfully')
      if (onSuccess) await onSuccess()
    } catch (err) {
      bulkError.value = err.message
    } finally {
      bulkActionInProgress.value = false
    }
  }

  async function applyBulkDelete(onSuccess) {
    if (selectedReports.value.length === 0) return
    bulkActionInProgress.value = true
    bulkError.value = null
    try {
      const res = await apiFetch('/api/reports/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'delete',
          report_ids: selectedReports.value
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to delete reports')
      }
      const data = await res.json()
      removeFromHistory(selectedReports.value)
      showDeleteModal.value = false
      selectedReports.value = []
      showSuccess(data.message || 'Reports deleted successfully')
      if (onSuccess) await onSuccess()
    } catch (err) {
      bulkError.value = err.message
    } finally {
      bulkActionInProgress.value = false
    }
  }

  async function applyBulkArchive({ name, description, filters, removeFromActive = true }, onSuccess) {
    if (selectedReports.value.length === 0) return
    bulkActionInProgress.value = true
    bulkError.value = null
    try {
      const res = await apiFetch('/api/archives', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_ids: selectedReports.value,
          name: name || undefined,
          description: description || undefined,
          filters: filters || {},
          remove_from_active: removeFromActive
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to create archive')
      }
      const data = await res.json()
      if (removeFromActive) {
        removeFromHistory(selectedReports.value)
      }
      showArchiveModal.value = false
      selectedReports.value = []
      showSuccess(`Archive "${data.name}" created with ${data.report_count} report(s)`)
      if (onSuccess) await onSuccess()
    } catch (err) {
      bulkError.value = err.message
    } finally {
      bulkActionInProgress.value = false
    }
  }

  async function removeTagFromReport({ report, tag }, onSuccess) {
    if (!report?.id || !tag) return
    try {
      const encodedId = encodeURIComponent(report.id)
      const encodedTag = encodeURIComponent(tag)
      const res = await apiFetch(`/api/reports/${encodedId}/label/${encodedTag}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        if (Array.isArray(report.tags)) {
          report.tags = report.tags.filter(t => t !== tag)
        }
        if (Array.isArray(report.labels)) {
          report.labels = report.labels.filter(t => t !== tag)
        }
        showSuccess(`Removed tag '${tag}' from report`, 3000)
        if (onSuccess) await onSuccess()
      }
    } catch (err) {
      console.error('Failed to remove tag', err)
    }
  }

  return {
    selectedReports,
    bulkActionInProgress,
    bulkError,
    bulkSuccessMessage,
    showLabelModal,
    showUnlabelModal,
    showAuthorModal,
    showArchiveModal,
    showDeleteModal,
    targetReportIdForAuthor,
    authorInitialValue,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    openLabelModal,
    openUnlabelModal,
    openAuthorModal,
    openArchiveModal,
    openDeleteModal,
    applyBulkLabel,
    applyBulkUnlabel,
    applyAuthor,
    applyBulkDelete,
    applyBulkArchive,
    removeTagFromReport
  }
}
