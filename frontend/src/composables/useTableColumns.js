import { ref, computed, onUnmounted } from 'vue'

const DEFAULT_COLUMNS = [
  { key: 'select', label: '', width: 48, minWidth: 48, resizable: false },
  { key: 'platform', label: 'Platform', width: 130, minWidth: 70, resizable: true },
  { key: 'qubits', label: 'Qubits', width: 100, minWidth: 60, resizable: true },
  { key: 'protocols', label: 'Protocols', width: 260, minWidth: 120, resizable: true },
  { key: 'tags', label: 'Tags', width: 190, minWidth: 90, resizable: true },
  { key: 'author', label: 'Author', width: 120, minWidth: 70, resizable: true },
  { key: 'date', label: 'Date', width: 130, minWidth: 80, resizable: true }
]

const STORAGE_KEY = 'qibocal_report_table_columns_v1'

/**
 * Composable for managing resizable report table columns with persistence.
 */
export function useTableColumns(customDefaults = DEFAULT_COLUMNS, storageKey = STORAGE_KEY) {
  function loadSavedWidths() {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved)
        return customDefaults.map(col => {
          if (parsed[col.key] && typeof parsed[col.key] === 'number') {
            return { ...col, width: Math.max(col.minWidth, parsed[col.key]) }
          }
          return { ...col }
        })
      }
    } catch {
      // Ignore localStorage errors
    }
    return customDefaults.map(col => ({ ...col }))
  }

  const columns = ref(loadSavedWidths())

  const totalTableWidth = computed(() => {
    return columns.value.reduce((acc, c) => acc + c.width, 0)
  })

  function saveWidths() {
    try {
      const map = {}
      columns.value.forEach(col => {
        map[col.key] = col.width
      })
      localStorage.setItem(storageKey, JSON.stringify(map))
    } catch {
      // Ignore localStorage errors
    }
  }

  function resetColumnWidth(index) {
    if (customDefaults[index]) {
      columns.value[index].width = customDefaults[index].width
      saveWidths()
    }
  }

  const resizingIndex = ref(-1)
  let startX = 0
  let startWidth = 0

  function handleMouseMove(e) {
    if (resizingIndex.value < 0) return
    const col = columns.value[resizingIndex.value]
    const delta = e.clientX - startX
    col.width = Math.max(col.minWidth, startWidth + delta)
  }

  function handleMouseUp() {
    if (resizingIndex.value >= 0) {
      saveWidths()
      resizingIndex.value = -1
    }
    document.body.style.cursor = ''
    document.body.style.userSelect = ''

    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('mouseup', handleMouseUp)
  }

  function startResize(index, e) {
    resizingIndex.value = index
    startX = e.clientX
    startWidth = columns.value[index].width

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }

  onUnmounted(() => {
    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  })

  return {
    columns,
    totalTableWidth,
    resizingIndex,
    startResize,
    resetColumnWidth
  }
}
