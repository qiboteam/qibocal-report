import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { parse } from 'vue/compiler-sfc'

/** The elements of a template under `node`, depth first. */
function* descendants(node) {
  for (const child of node.children || []) {
    yield child
    yield * descendants(child)
  }
}

const conditional = node => (node.props || []).some(prop => prop.type === 7 && ['if', 'else', 'else-if'].includes(prop.name))

test('the upload dialog of a report renders whether the sidebar is expanded or collapsed', () => {
  const source = readFileSync(new URL('../src/components/sidebar/SidebarProtocols.vue', import.meta.url), 'utf8')
  const roots = parse(source).descriptor.template.ast.children.filter(node => node.type === 1)
  const layouts = roots.filter(conditional)
  assert.equal(layouts.length, 2, 'the expanded layout and the collapsed one')
  const inLayout = name => layouts.some(layout => [...descendants(layout)].some(node => node.tag === name))
  // The button is in the expanded layout; the dialog must not hide in either.
  assert.ok([...descendants(layouts[0])].some(node => node.tag === 'button' && /Upload to another server/.test(node.loc.source)))
  assert.equal(inLayout('upload-modal'), false, 'outside both layouts')
  assert.ok(roots.some(node => [node, ...descendants(node)].some(inner => inner.tag === 'upload-modal')), 'rendered at all')
})
