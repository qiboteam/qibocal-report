import assert from 'node:assert/strict'
import { test } from 'node:test'

import { cleanTree, elementAction, keptAttribute, safeUrl, sanitizeHtml } from '../src/utils/sanitize.js'

// No DOM under node: a tree with the few members the walk uses.
class Node {
  constructor(nodeType, parent = null) {
    this.nodeType = nodeType
    this.parent = parent
  }

  remove() {
    const siblings = this.parent.childNodes
    siblings.splice(siblings.indexOf(this), 1)
  }

  replaceWith(...nodes) {
    const siblings = this.parent.childNodes
    for (const node of nodes) node.parent = this.parent
    siblings.splice(siblings.indexOf(this), 1, ...nodes)
  }
}

class Element extends Node {
  constructor(tagName, attributes = {}, children = []) {
    super(1)
    this.tagName = tagName.toUpperCase()
    this.attrs = new Map(Object.entries(attributes))
    this.childNodes = []
    for (const child of children) this.append(child)
  }

  append(child) {
    child.parent = this
    this.childNodes.push(child)
  }

  get attributes() { return [...this.attrs.keys()].map(name => ({ name })) }
  getAttribute(name) { return this.attrs.has(name) ? this.attrs.get(name) : null }
  setAttribute(name, value) { this.attrs.set(name, String(value)) }
  removeAttribute(name) { this.attrs.delete(name) }
}

class Text extends Node {
  constructor(text) {
    super(3)
    this.text = text
  }
}

const el = (tag, attributes, ...children) => new Element(tag, attributes, children)
const text = value => new Text(value)

function render(node) {
  if (node.nodeType === 3) return node.text
  const attributes = [...node.attrs].map(([name, value]) => ` ${name}="${value}"`).join('')
  const tag = node.tagName.toLowerCase()
  return `<${tag}${attributes}>${node.childNodes.map(render).join('')}</${tag}>`
}

function clean(...children) {
  const body = el('body', {}, ...children)
  cleanTree(body)
  return body.childNodes.map(render).join('')
}

test("a protocol's table, as Qibocal writes it, comes through whole", () => {
  const table = el('div', { class: 'overflow-x-auto my-3' },
    el('table', { class: 'dataframe fitting-table', border: '1' },
      el('thead', {}, el('tr', { style: 'text-align: left;' }, el('th', { class: 'p-2' }, text('Qubit')))),
      el('tbody', {}, el('tr', {}, el('td', { colspan: '2' }, el('b', {}, text('Q4')), el('br'), text('0.17 ± 0.01'))))))
  assert.equal(clean(table),
    '<div class="overflow-x-auto my-3"><table class="dataframe fitting-table"><thead><tr style="text-align: left;">' +
    '<th class="p-2">Qubit</th></tr></thead><tbody><tr><td colspan="2"><b>Q4</b><br></br>0.17 ± 0.01</td></tr></tbody></table></div>')
})

test('code and other documents go with their content; unknown elements leave theirs', () => {
  assert.equal(clean(
    el('script', {}, text('steal()')),
    el('style', {}, text('body { display: none }')),
    el('iframe', { srcdoc: '<script>x()</script>' }),
    el('svg', { onload: 'x()' }, el('script', {}, text('x()'))),
    el('form', { action: 'https://evil.example' }, text('kept '), el('input', { value: 'x' }), el('button', {}, text('Go'))),
    el('font', { color: 'red' }, el('span', { onclick: 'x()' }, text('text')))
  ), 'kept <span>text</span>')
  assert.equal(elementAction('object'), 'drop')
  assert.equal(elementAction('meta'), 'drop')
  assert.equal(elementAction('marquee'), 'unwrap')
  assert.equal(elementAction('td'), 'keep')
})

test('handlers and unlisted attributes go; the presentational ones stay', () => {
  assert.equal(clean(el('td', {
    onclick: 'x()', onmouseover: 'x()', formaction: 'x', srcdoc: 'x', class: 'c', style: 'color: red',
    title: 't', id: 'i', rowspan: '2', align: 'left', width: '10', height: '5', 'data-x': 'y'
  })), '<td class="c" style="color: red" title="t" rowspan="2" align="left" width="10" height="5"></td>')
  assert.equal(keptAttribute('div', 'href', 'https://example.org'), false)
  assert.equal(keptAttribute('img', 'srcset', 'https://example.org/a.png 2x'), false)
})

test('links lead to the web, mail or the page, and open apart', () => {
  assert.equal(clean(el('a', { href: 'https://qibo.science', target: '_self' }, text('Qibo'))),
    '<a href="https://qibo.science" rel="noopener noreferrer" target="_blank">Qibo</a>')
  assert.equal(clean(el('a', { href: ' java\nscript:alert(1)' }, text('x'))), '<a>x</a>')
  assert.equal(clean(el('a', { href: '#fit' }, text('fit'))), '<a href="#fit">fit</a>')
  for (const url of ['http://a', 'HTTPS://a', 'mailto:a@b.c', '#x']) assert.equal(safeUrl(url), true, url)
  for (const url of ['javascript:x()', 'JaVaScRiPt:x()', 'data:text/html,x', 'vbscript:x', 'file:///etc/passwd', 'relative/page', '']) {
    assert.equal(safeUrl(url), false, url)
  }
  assert.equal(safeUrl('relative/page', { relative: true }), true)
  assert.equal(safeUrl('javascript:x()', { relative: true }), false)
})

test('images only from the web or inline raster data', () => {
  assert.equal(clean(el('img', { src: 'data:image/png;base64,AAAA', alt: 'plot', onerror: 'x()' })),
    '<img src="data:image/png;base64,AAAA" alt="plot"></img>')
  assert.equal(clean(el('img', { src: 'data:image/svg+xml,<svg onload=x()>' })), '')
  assert.equal(clean(el('img', { src: 'javascript:x()' })), '')
  for (const url of ['https://a/b.png', 'data:image/jpeg;base64,A', 'data:image/gif,A', 'data:image/webp;base64,A']) {
    assert.equal(safeUrl(url, { image: true }), true, url)
  }
  assert.equal(safeUrl('#x', { image: true }), false)
  assert.equal(safeUrl('logo.svg', { image: true, relative: true }), true)
})

test('comments and other nodes go', () => {
  const body = el('body', {}, text('a'), new Node(8), text('b'))
  body.childNodes[1].parent = body
  cleanTree(body)
  assert.equal(body.childNodes.map(render).join(''), 'ab')
})

test('without a DOM to parse with, the HTML is text', () => {
  assert.equal(sanitizeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror="alert(1)"&gt;')
  assert.equal(sanitizeHtml(''), '')
  assert.equal(sanitizeHtml(null), '')
})
