/**
 * Markdown for what users write — comments — rendered with raw HTML
 * neutralised: a `<` in the source is text, never a tag, so a comment can
 * carry emphasis, code, lists and links, and nothing that runs. Links open
 * in a new tab and only lead to http(s) or mail addresses.
 */
import { marked } from 'marked'

const renderer = new marked.Renderer()

renderer.link = (href, title, text) => {
  const safe = /^(https?:|mailto:)/i.test(String(href || '').trim()) ? href : null
  if (!safe) return text
  const label = title ? ` title="${String(title).replace(/"/g, '&quot;')}"` : ''
  return `<a href="${safe}" target="_blank" rel="noopener noreferrer"${label}>${text}</a>`
}

// No images: a comment is text; an image would also be a request to a third party.
renderer.image = (_href, _title, text) => text || ''

export function renderMarkdown(source) {
  const text = String(source ?? '').replace(/</g, '&lt;')
  return marked.parse(text, { renderer, gfm: true, breaks: true })
}

/** The distance from now, in words, for a comment's time. */
export function timeAgo(timestamp, now = Date.now()) {
  const at = new Date(timestamp).getTime()
  if (!Number.isFinite(at)) return ''
  const elapsed = Math.max(0, now - at)
  const minute = 60_000
  const hour = 60 * minute
  const day = 24 * hour
  const unit = (amount, name) => `${amount} ${name}${amount === 1 ? '' : 's'} ago`
  if (elapsed < minute) return 'just now'
  if (elapsed < hour) return unit(Math.floor(elapsed / minute), 'minute')
  if (elapsed < day) return unit(Math.floor(elapsed / hour), 'hour')
  if (elapsed < 30 * day) return unit(Math.floor(elapsed / day), 'day')
  return new Date(at).toLocaleDateString()
}
