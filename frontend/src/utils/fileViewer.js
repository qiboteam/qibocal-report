import { reactive } from 'vue'

/**
 * A file shown over the page, where no tab can open — inside the desktop
 * application, or a browser refusing the pop-up: its name, and its text as
 * it reads best. One for the whole dashboard, mounted once.
 */
export const fileViewer = reactive({ open: false, name: '', text: '' })

/** The text of a file as it reads best: JSON indented, anything else as it is. */
export function readableText(text, contentType = '') {
  const looksJson = /json/i.test(contentType) || /^\s*[[{]/.test(text)
  if (!looksJson) return text
  try {
    return JSON.stringify(JSON.parse(text), null, 2)
  } catch {
    return text
  }
}

export function showFile(name, text, contentType = '') {
  Object.assign(fileViewer, { open: true, name, text: readableText(text, contentType) })
}

export function closeFile() {
  Object.assign(fileViewer, { open: false, name: '', text: '' })
}
