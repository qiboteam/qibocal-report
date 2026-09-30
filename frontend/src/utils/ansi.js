const COLORS = [
  '#1e1e1e', '#f48771', '#89d185', '#e5c07b',
  '#6cb6ff', '#c586c0', '#56d4dd', '#d4d4d4',
  '#808080', '#ff8080', '#b5e890', '#ffe080',
  '#9cdcfe', '#e2a8ef', '#80e5ed', '#ffffff'
]

function indexedColor(index) {
  if (index < 16) return COLORS[index]
  if (index >= 232) {
    const gray = 8 + (index - 232) * 10
    return `rgb(${gray}, ${gray}, ${gray})`
  }
  const value = index - 16
  const level = n => n === 0 ? 0 : 55 + n * 40
  return `rgb(${level(Math.floor(value / 36))}, ${level(Math.floor(value / 6) % 6)}, ${level(value % 6)})`
}

// Only SGR styling is interpreted; terminal commands and OSC links are discarded.
export function ansiSegments(text) {
  const clean = String(text || '')
    .replace(/\x1b\](?:[^\x07\x1b]|\x1b(?!\\))*(?:\x07|\x1b\\)/g, '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
  const sequence = /\x1b\[([0-9;:]*)([ -/]*)([@-~])|\x1b[@-_]|[\x00-\x08\x0b-\x1f\x7f]/g
  const segments = []
  let style = {}
  let reverse = false
  let offset = 0
  const segmentStyle = () => reverse ? {
    ...style,
    color: style.backgroundColor || '#1e1e1e',
    backgroundColor: style.color || '#d4d4d4'
  } : { ...style }
  for (const match of clean.matchAll(sequence)) {
    if (match.index > offset) segments.push({ text: clean.slice(offset, match.index), style: segmentStyle() })
    offset = match.index + match[0].length
    if (match[3] !== 'm') continue
    const codes = (match[1] || '0').split(/[;:]/).map(Number)
    for (let i = 0; i < codes.length; i++) {
      const code = codes[i]
      if (code === 0) { style = {}; reverse = false }
      else if (code === 1) style.fontWeight = 'bold'
      else if (code === 2) style.opacity = '0.65'
      else if (code === 3) style.fontStyle = 'italic'
      else if (code === 4) style.textDecoration = 'underline'
      else if (code === 7) reverse = true
      else if (code === 9) style.textDecoration = 'line-through'
      else if (code === 22) { delete style.fontWeight; delete style.opacity }
      else if (code === 23) delete style.fontStyle
      else if (code === 24 || code === 29) delete style.textDecoration
      else if (code === 27) reverse = false
      else if (code === 39) delete style.color
      else if (code === 49) delete style.backgroundColor
      else if (code >= 30 && code <= 37) style.color = COLORS[code - 30]
      else if (code >= 90 && code <= 97) style.color = COLORS[code - 90 + 8]
      else if (code >= 40 && code <= 47) style.backgroundColor = COLORS[code - 40]
      else if (code >= 100 && code <= 107) style.backgroundColor = COLORS[code - 100 + 8]
      else if (code === 38 || code === 48) {
        const property = code === 38 ? 'color' : 'backgroundColor'
        const mode = codes[++i]
        if (mode === 5) {
          const index = codes[++i]
          if (Number.isInteger(index) && index >= 0 && index <= 255) style[property] = indexedColor(index)
        } else if (mode === 2) {
          const rgb = codes.slice(i + 1, i + 4)
          i += 3
          if (rgb.length === 3 && rgb.every(n => Number.isInteger(n) && n >= 0 && n <= 255)) {
            style[property] = `rgb(${rgb.join(', ')})`
          }
        }
      }
    }
  }
  if (offset < clean.length) segments.push({ text: clean.slice(offset), style: segmentStyle() })
  return segments
}
