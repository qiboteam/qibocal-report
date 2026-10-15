<!--
  The launcher's own guide, inside the launcher: the keyboard first, since
  it is the one thing the pages cannot show, then the user guide as it is
  published — the very same Markdown, rendered here — so the application
  documents itself the way the dashboard does with its Documentation.
-->
<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div>
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Help</h1>
      <p class="mt-1 text-xs text-gray-500">
        How the launcher works, section by section, and every keyboard shortcut. The same guide is published at
        <button type="button" class="text-[#833dff] hover:text-[#6b21a8] transition" @click="openExternal(GUIDE_URL)">{{ GUIDE_URL }}</button>.
      </p>
    </div>

    <section id="keyboard" class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-1">Keyboard shortcuts</h2>
      <p class="text-xs text-gray-500 mb-4">
        Letters work anywhere but in a text field, on the launcher's pages and on the dashboard's alike:
        <kbd class="lx-kbd">g</kbd> then a letter goes to a section, as on GitHub; <kbd class="lx-kbd">?</kbd> shows the list
        over any page. The menu shortcuts work everywhere, text fields included.
      </p>
      <div class="grid gap-x-8 gap-y-4 sm:grid-cols-3">
        <div v-for="group in groups" :key="group.name">
          <p class="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">{{ group.name }}</p>
          <dl class="space-y-1.5">
            <div v-for="shortcut in group.entries" :key="shortcut.what" class="flex items-start gap-2 text-xs">
              <dt class="shrink-0 whitespace-nowrap">
                <kbd v-for="key in describeKeys(shortcut.keys)" :key="key" class="lx-kbd">{{ key }}</kbd>
              </dt>
              <dd class="text-gray-700 min-w-0">{{ shortcut.what }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- The keys that mean something on one page only. -->
      <h3 class="text-xs font-semibold text-gray-900 mt-6 mb-1">On each page</h3>
      <p class="text-xs text-gray-500 mb-4">
        <kbd class="lx-kbd">j</kbd> and <kbd class="lx-kbd">k</kbd> walk the page's list — the entry under the cursor
        wears an outline — and a letter acts on it. <kbd class="lx-kbd">Esc</kbd> clears the cursor.
      </p>
      <div class="grid gap-x-8 gap-y-5 sm:grid-cols-2">
        <div v-for="page in pages" :key="page.title">
          <p class="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">{{ page.title }}</p>
          <dl class="space-y-1.5">
            <div v-for="shortcut in page.entries" :key="shortcut.what" class="flex items-start gap-2 text-xs">
              <dt class="shrink-0 whitespace-nowrap">
                <kbd v-for="key in describeKeys(shortcut.keys)" :key="key" class="lx-kbd">{{ key }}</kbd>
              </dt>
              <dd class="text-gray-700 min-w-0">{{ shortcut.what }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <!-- The guide: on this page, the headings are the table of contents. -->
    <section class="bm-card p-5">
      <nav class="mb-5 flex flex-wrap gap-x-3 gap-y-1 text-xs">
        <a v-for="heading in headings" :key="heading.id" :href="`#${heading.id}`" class="text-[#833dff] hover:text-[#3b107e] transition" @click.prevent="jump(heading.id)">
          {{ heading.text }}
        </a>
      </nav>
      <article ref="article" class="lx-prose" @click="follow" v-html="html" />
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { marked } from 'marked'
import guide from '../../../docs/user-guide/launcher.md?raw'
import { openExternal } from '../bridge.js'
import { SHORTCUTS, describeKeys } from '../shortcuts.js'
import { PAGE_KEYS, pageShortcuts } from '../pagekeys.js'

const pages = Object.keys(PAGE_KEYS).map(pageShortcuts)

const GUIDE_URL = 'https://qibo.science/qibocal-report/user-guide/launcher/'

const article = ref(null)

const groups = computed(() => {
  const byName = new Map()
  for (const shortcut of SHORTCUTS) {
    if (!byName.has(shortcut.group)) byName.set(shortcut.group, { name: shortcut.group, entries: [] })
    byName.get(shortcut.group).entries.push(shortcut)
  }
  return [...byName.values()]
})

/** The anchor of a heading, as the published site derives it: lowercase, hyphens, no emoji. */
function slug(text) {
  return String(text)
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .trim()
    .replace(/\s+/g, '-')
}

const headings = []
const renderer = new marked.Renderer()
renderer.heading = (text, level) => {
  const id = slug(text)
  if (level === 2) headings.push({ id, text: text.replace(/^[^\p{L}\p{N}]+/u, '').trim() })
  return `<h${level} id="${id}">${text}</h${level}>\n`
}
const html = marked.parse(guide, { renderer, gfm: true, breaks: false })

function jump(id) {
  article.value?.querySelector(`#${CSS.escape(id)}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/** Links in the guide: anchors scroll here, everything else opens outside. */
function follow(event) {
  const anchor = event.target?.closest?.('a[href]')
  if (!anchor) return
  const href = anchor.getAttribute('href') || ''
  event.preventDefault()
  if (href.startsWith('#')) {
    jump(href.slice(1))
    return
  }
  const target = /^https?:/.test(href) ? href : new URL(href, GUIDE_URL).href
  openExternal(target)
}
</script>
