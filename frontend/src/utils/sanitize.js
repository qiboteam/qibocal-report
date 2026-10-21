/**
 * HTML a server sends — a protocol's tables, a documentation page — made
 * safe to bind with `v-html`. Reports travel between servers, and this page
 * holds every server's token, so nothing in it may run: the HTML is parsed
 * into a document of its own, where scripts do not run, and walked against
 * an allowlist. Elements off the list are unwrapped to their content, those
 * that carry code or other documents dropped with it; attributes off the
 * list go, and links and images only lead where they should.
 */

const KEPT = new Set([
  'div', 'span', 'p', 'br', 'hr', 'b', 'i', 'strong', 'em', 'u', 'small', 'sup', 'sub', 'code', 'pre',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
  'a', 'img', 'figure', 'figcaption', 'details', 'summary', 'blockquote'
])

/** Dropped with their content: code, styles, other documents, controls. */
const DROPPED = new Set([
  'script', 'style', 'iframe', 'frame', 'frameset', 'object', 'embed', 'applet', 'portal',
  'noscript', 'noembed', 'noframes', 'template', 'svg', 'math', 'link', 'meta', 'base', 'title',
  'input', 'button', 'textarea', 'select', 'option', 'datalist', 'xmp', 'plaintext',
  'audio', 'video', 'canvas'
])

const ATTRIBUTES = new Set(['class', 'style', 'title', 'alt', 'colspan', 'rowspan', 'align', 'width', 'height'])

const ELEMENT_NODE = 1
const TEXT_NODE = 3

/** What becomes of an element: 'keep', 'unwrap' to its content, or 'drop' with it. */
export function elementAction(tag) {
  if (KEPT.has(tag)) return 'keep'
  if (DROPPED.has(tag)) return 'drop'
  return 'unwrap'
}

/**
 * Whether a link or image address may stay: http(s), mail and fragments;
 * for images, inline raster data too; relative addresses only when asked.
 */
export function safeUrl(value, { image = false, relative = false } = {}) {
  // Browsers ignore whitespace and control characters in a scheme: so does this.
  const url = String(value ?? '').replace(/[\u0000- \u007f-\u009f]/g, '')
  if (!url) return false
  if (url.startsWith('#')) return !image
  const scheme = url.match(/^([a-z][a-z0-9+.-]*):/i)
  if (!scheme) return relative
  const name = scheme[1].toLowerCase()
  if (image) return name === 'http' || name === 'https' || /^data:image\/(png|jpeg|gif|webp)[;,]/i.test(url)
  return name === 'http' || name === 'https' || name === 'mailto'
}

/** Whether an attribute of a kept element stays. */
export function keptAttribute(tag, name, value, options = {}) {
  if (ATTRIBUTES.has(name)) return true
  if (tag === 'a' && name === 'href') return safeUrl(value, { relative: options.relative })
  if (tag === 'img' && name === 'src') return safeUrl(value, { image: true, relative: options.relative })
  return false
}

function cleanAttributes(node, tag, options) {
  for (const { name } of Array.from(node.attributes)) {
    if (!keptAttribute(tag, name.toLowerCase(), node.getAttribute(name), options)) node.removeAttribute(name)
  }
  if (tag === 'a' && node.getAttribute('href') && !node.getAttribute('href').startsWith('#')) {
    node.setAttribute('rel', 'noopener noreferrer')
    node.setAttribute('target', '_blank')
  }
}

/**
 * Clean the children of `parent` in place. Over any tree with the few DOM
 * members used here — `nodeType`, `tagName`, `childNodes`, `attributes`,
 * `getAttribute`, `setAttribute`, `removeAttribute`, `remove`, `replaceWith`.
 */
export function cleanTree(parent, options = {}) {
  for (const node of Array.from(parent.childNodes)) {
    if (node.nodeType === TEXT_NODE) continue
    if (node.nodeType !== ELEMENT_NODE) {
      node.remove()
      continue
    }
    const tag = String(node.tagName).toLowerCase()
    const action = elementAction(tag)
    if (action === 'drop') {
      node.remove()
      continue
    }
    cleanTree(node, options)
    if (action === 'unwrap') {
      node.replaceWith(...Array.from(node.childNodes))
      continue
    }
    cleanAttributes(node, tag, options)
    if (tag === 'img' && !node.getAttribute('src')) node.remove()
  }
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/**
 * The HTML, safe to bind. `relative` keeps relative links and images, for
 * pages whose clicks are handled here, as the documentation's are. Without
 * a DOM to parse with, the HTML is shown as text.
 */
export function sanitizeHtml(html, { relative = false } = {}) {
  if (!html) return ''
  if (typeof DOMParser === 'undefined') return escapeHtml(String(html))
  const doc = new DOMParser().parseFromString(String(html), 'text/html')
  cleanTree(doc.body, { relative })
  return doc.body.innerHTML
}
