/**
 * Reading and editing the configuration files as *entries*, not as text.
 *
 * The four shared files hold two shapes only — a list of objects
 * (`servers.json`) and a map of named things (`notebooks.json`,
 * `launcher.json`, `auth.json`) — so one editor serves them all, provided it
 * can name what it shows. That is what this module does: it turns a parsed
 * document into entries with a title, and an entry into labelled fields,
 * reusing the descriptions the rest of the launcher already carries.
 *
 * Everything here is pure, and covered by `tests/config.test.js`.
 */
import { NOTEBOOK_FIELDS, describeConnection } from './notebooks.js'

/** What each known file contains, and how to speak about it. */
export const CONFIG_SHAPES = {
  'servers.json': {
    kind: 'list',
    entry: 'server',
    /** Fields shown first, in this order, whether or not they are present. */
    known: [
      { name: 'name', label: 'Name', type: 'text' },
      { name: 'url', label: 'Address', type: 'text', mono: true },
      { name: 'description', label: 'Description', type: 'text' },
      { name: 'avatar', label: 'Avatar', type: 'text' }
    ],
    template: () => ({
      id: `srv-${Math.random().toString(36).slice(2, 10)}`,
      name: '',
      url: '',
      description: '',
      avatar: 'quantum-ring',
      created_at: new Date().toISOString()
    })
  },
  'notebooks.json': {
    kind: 'map',
    entry: 'connection',
    known: NOTEBOOK_FIELDS.map(field => ({
      name: field.name,
      label: field.label,
      help: field.help,
      type: field.type === 'choice' ? 'boolean' : field.type
    })),
    template: () => ({ ssh: '' })
  },
  'launcher.json': {
    kind: 'map',
    entry: 'preference',
    known: [
      { name: 'executable', label: 'qibocal-report executable', type: 'text', mono: true },
      { name: 'package', label: 'qibocal-report to install', type: 'text', mono: true },
      { name: 'launches', label: 'Remembered server launches', type: 'json' }
    ]
  },
  'auth.json': {
    kind: 'map',
    entry: 'section',
    known: [],
    warning:
      'Users, invitations and signing keys. Changing the keys signs everyone ' +
      'out, exactly as deleting the file does.'
  }
}

export function shapeOf(file) {
  return CONFIG_SHAPES[file] || { kind: 'map', entry: 'entry', known: [] }
}

/** The empty document of a file, used when it does not exist yet. */
export function emptyDocument(file) {
  return shapeOf(file).kind === 'list' ? [] : {}
}

/**
 * Parse an editor buffer, answering the error instead of raising it.
 *
 * An empty buffer is the file that was never written, not a mistake.
 */
export function parseDocument(file, text) {
  if (typeof text !== 'string' || !text.trim()) {
    return { value: emptyDocument(file), error: null }
  }
  let parsed
  try {
    parsed = JSON.parse(text)
  } catch (error) {
    return { value: null, error: error.message }
  }
  const expected = shapeOf(file).kind
  const found = Array.isArray(parsed) ? 'list' : parsed && typeof parsed === 'object' ? 'map' : 'other'
  if (found !== expected) {
    return {
      value: null,
      error: expected === 'list'
        ? `${file} must hold a list of entries.`
        : `${file} must hold an object of named entries.`
    }
  }
  return { value: parsed, error: null }
}

export function formatDocument(value) {
  return `${JSON.stringify(value, null, 2)}\n`
}

function firstString(...candidates) {
  return candidates.find(candidate => typeof candidate === 'string' && candidate.trim()) || ''
}

/** One-line summary of an entry, so the list reads without unfolding it. */
function summarize(file, key, entry) {
  if (file === 'notebooks.json' && entry && typeof entry === 'object') return describeConnection(entry)
  if (file === 'servers.json') return firstString(entry?.url, entry?.description)
  if (entry === null || entry === undefined) return 'empty'
  if (Array.isArray(entry)) return `${entry.length} item${entry.length === 1 ? '' : 's'}`
  if (typeof entry === 'object') {
    const keys = Object.keys(entry)
    return keys.length ? `${keys.length} key${keys.length === 1 ? '' : 's'}: ${keys.slice(0, 4).join(', ')}` : 'empty'
  }
  return String(entry)
}

/**
 * The entries of a document: list positions for `servers.json`, keys for the
 * others. The key is what every other function here takes back.
 */
export function describeEntries(file, value) {
  if (shapeOf(file).kind === 'list') {
    return (Array.isArray(value) ? value : []).map((entry, index) => ({
      key: String(index),
      title: firstString(entry?.name, entry?.url, `Entry ${index + 1}`),
      subtitle: summarize(file, String(index), entry),
      value: entry
    }))
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) return []
  return Object.entries(value).map(([key, entry]) => ({
    key,
    title: key,
    subtitle: summarize(file, key, entry),
    value: entry
  }))
}

function fieldType(value) {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  if (value === null || typeof value === 'string') return 'text'
  return 'json'
}

/**
 * The editable fields of one entry: the ones the file is known to carry
 * first, labelled, then whatever else the file happens to hold.
 */
export function entryFields(file, entry) {
  if (entry === null || typeof entry !== 'object' || Array.isArray(entry)) {
    // A scalar preference, or a list: a single field holding the whole value.
    return [{ name: '', label: 'Value', type: fieldType(entry), value: entry }]
  }
  const known = shapeOf(file).known
  const blank = { boolean: false, number: null, json: null, text: '' }
  const fields = known
    // A server always offers its four fields, even the ones it lacks: the
    // editor is also where a missing name or description is filled in.
    .filter(field => entry[field.name] !== undefined || file === 'servers.json')
    .map(field => {
      const value = entry[field.name]
      return {
        ...field,
        type: value === undefined ? field.type : fieldType(value),
        value: value === undefined ? blank[field.type] ?? '' : value
      }
    })
  const covered = new Set(known.map(field => field.name))
  for (const [name, value] of Object.entries(entry)) {
    if (covered.has(name)) continue
    fields.push({ name, label: name, type: fieldType(value), value })
  }
  return fields
}

function withEntry(file, value, key, entry) {
  if (shapeOf(file).kind === 'list') {
    const list = Array.isArray(value) ? [...value] : []
    const index = Number(key)
    if (!Number.isInteger(index) || index < 0 || index >= list.length) return list
    list[index] = entry
    return list
  }
  return { ...(value || {}), [key]: entry }
}

/** Replace one field of one entry, leaving everything else untouched. */
export function updateEntry(file, value, key, name, fieldValue) {
  const entries = describeEntries(file, value)
  const current = entries.find(entry => entry.key === key)
  if (!current) return value
  if (!name) return withEntry(file, value, key, fieldValue)
  const updated = { ...(current.value || {}), [name]: fieldValue }
  return withEntry(file, value, key, updated)
}

/** Rename a map entry, keeping its position among the others. */
export function renameEntry(file, value, key, name) {
  if (shapeOf(file).kind === 'list' || key === name) return value
  const trimmed = typeof name === 'string' ? name.trim() : ''
  if (!trimmed || !value || value[trimmed] !== undefined) return value
  return Object.fromEntries(
    Object.entries(value).map(([current, entry]) => [current === key ? trimmed : current, entry])
  )
}

export function removeEntry(file, value, key) {
  if (shapeOf(file).kind === 'list') {
    const index = Number(key)
    return (Array.isArray(value) ? value : []).filter((_, position) => position !== index)
  }
  const { [key]: _removed, ...rest } = value || {}
  return rest
}

/** Append an entry of the shape the file expects, answering its key too. */
export function addEntry(file, value, name = '') {
  const shape = shapeOf(file)
  const template = shape.template ? shape.template() : {}
  if (shape.kind === 'list') {
    const list = [...(Array.isArray(value) ? value : []), template]
    return { value: list, key: String(list.length - 1) }
  }
  const existing = value && typeof value === 'object' ? value : {}
  const base = (typeof name === 'string' && name.trim()) || `new-${shape.entry}`
  let key = base
  let suffix = 2
  while (existing[key] !== undefined) key = `${base}-${suffix++}`
  return { value: { ...existing, [key]: template }, key }
}
