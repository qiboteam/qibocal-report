import { apiFetch } from '../api.js'
import { state } from '../store.js'
import { inDesktop } from './desktop.js'
import { showFile } from './fileViewer.js'

async function fetchFile(path, server) {
  const response = await apiFetch(path, { cache: 'no-store' }, server)
  if (!response.ok) {
    const data = response.headers.get('Content-Type')?.includes('application/json')
      ? await response.json()
      : null
    throw new Error(typeof data?.detail === 'string'
      ? data.detail
      : `Failed to fetch file (${response.status})`)
  }
  return response
}

function getFilename(response, fallback) {
  const disposition = response.headers.get('Content-Disposition') || ''
  const encoded = disposition.match(/(?:^|;)\s*filename\*=utf-8''([^;]+)/i)
  if (encoded) return decodeURIComponent(encoded[1].trim())
  const plain = disposition.match(/(?:^|;)\s*filename=(?:"([^"]*)"|([^;]*))/i)
  return plain?.[1] || plain?.[2]?.trim() || fallback
}

function releaseUrlLater(url) {
  // Navigation and downloads consume blob URLs asynchronously.
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

export function getReportDownloadFilename(reportId, suffix = '') {
  const name = (reportId || 'report').split('/').pop().replaceAll(':', '-')
  return `${name}${suffix}.zip`
}

export async function downloadApiFile(path, filename = 'download.zip', server = state.activeServer) {
  const response = await fetchFile(path, server)
  const name = getFilename(response, filename)
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = name
  try {
    document.body.appendChild(link)
    link.click()
  } finally {
    link.remove()
    releaseUrlLater(url)
  }
  return name
}

/** A file shown over the page: where no tab can open, inside the application or past a pop-up blocker. */
async function viewApiFile(path, name, server) {
  const response = await fetchFile(path, server)
  showFile(getFilename(response, name), await response.text(), response.headers.get('Content-Type') || '')
}

/**
 * Show a file: in a tab of its own in a browser; over the page inside the
 * desktop application, which opens no tab, or when the browser refuses one.
 */
export async function openApiFile(path, server = state.activeServer, name = path.split('/').pop() || 'file') {
  if (inDesktop()) return viewApiFile(path, name, server)
  // Reserve the tab during the click, before awaiting a network request.
  const tab = window.open('about:blank', '_blank')
  if (!tab) return viewApiFile(path, name, server)
  tab.opener = null
  let url
  try {
    const response = await fetchFile(path, server)
    const blob = await response.blob()
    if (tab.closed) throw new Error('The file preview tab was closed.')
    url = URL.createObjectURL(blob)
    tab.location.replace(url)
    releaseUrlLater(url)
  } catch (err) {
    if (url) URL.revokeObjectURL(url)
    tab.close()
    throw err
  }
}
