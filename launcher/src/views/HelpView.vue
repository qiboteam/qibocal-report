<!--
  The launcher's own guide, inside the launcher, laid out as the dashboard's
  Documentation is: the pages in a sidebar, one at a time, with the previous
  and the next at its foot. The pages are the Desktop Launcher section of the
  documentation — the very same Markdown — and the keyboard page carries the
  live list of shortcuts above its text, since it is the one thing the other
  pages cannot show.
-->
<template>
  <div class="max-w-6xl mx-auto px-5 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <aside class="lg:col-span-3 bm-card p-4 lg:sticky lg:top-4">
        <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3">Help</h2>
        <nav class="space-y-0.5" aria-label="Help pages">
          <button
            v-for="(item, index) in pages"
            :key="item.name"
            type="button"
            class="w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition flex items-center justify-between group cursor-pointer"
            :class="item.name === current.name
              ? 'bg-purple-50 text-[#833dff] font-semibold border-l-2 border-[#833dff]'
              : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
            :aria-current="item.name === current.name ? 'page' : undefined"
            @click="open(item.name)"
          >
            <span class="truncate">{{ item.title }}</span>
            <span v-if="index === 0" class="sr-only">(overview)</span>
          </button>
        </nav>
      </aside>

      <main class="lg:col-span-9 bm-card p-6 sm:p-8">
        <!-- Where this page is: the guide, then the page. -->
        <nav aria-label="Breadcrumbs" class="flex flex-wrap items-center gap-1.5 text-xs text-gray-500 mb-5 pb-4 border-b border-gray-100">
          <button type="button" class="font-medium hover:text-[#833dff] transition cursor-pointer" @click="open('index')">Desktop Launcher</button>
          <template v-if="current.name !== 'index'">
            <span class="text-gray-300">/</span>
            <span class="font-semibold text-gray-800">{{ current.title }}</span>
          </template>
        </nav>

        <h1 class="text-xl font-semibold text-gray-900 tracking-tight mb-4">{{ current.title }}</h1>

        <!-- The keyboard page: the live list first, from the very tables the keys are bound by. -->
        <section v-if="current.name === 'keyboard'" class="mb-6">
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
          <h2 class="text-xs font-semibold text-gray-900 mt-6 mb-3">On each page</h2>
          <div class="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            <div v-for="page in pageKeys" :key="page.title">
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

        <article ref="article" class="lx-prose" @click="follow" v-html="html" />

        <!-- The previous and the next page, as at the foot of the dashboard's Documentation. -->
        <div class="mt-10 pt-5 border-t border-gray-100 flex items-center justify-between gap-4">
          <button
            v-if="previous"
            type="button"
            class="flex flex-col items-start px-4 py-2.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 text-left transition group cursor-pointer"
            @click="open(previous.name)"
          >
            <span class="text-[10px] uppercase font-bold text-gray-400 group-hover:text-[#833dff]">← Previous</span>
            <span class="text-xs font-semibold text-gray-800 group-hover:text-[#833dff]">{{ previous.title }}</span>
          </button>
          <span v-else />
          <button
            v-if="next"
            type="button"
            class="flex flex-col items-end px-4 py-2.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 text-right transition group cursor-pointer"
            @click="open(next.name)"
          >
            <span class="text-[10px] uppercase font-bold text-gray-400 group-hover:text-[#833dff]">Next →</span>
            <span class="text-xs font-semibold text-gray-800 group-hover:text-[#833dff]">{{ next.title }}</span>
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { openExternal } from '../bridge.js'
import { SHORTCUTS, describeKeys } from '../shortcuts.js'
import { PAGE_KEYS, pageShortcuts } from '../pagekeys.js'
import { helpPages, helpTarget } from '../lib/help.js'

const sources = import.meta.glob('../../../docs/user-guide/launcher/*.md', { query: '?raw', import: 'default', eager: true })
const markdown = name => sources[`../../../docs/user-guide/launcher/${name}.md`] || ''

const route = useRoute()
const router = useRouter()
const article = ref(null)

const pages = helpPages()
const pageKeys = Object.keys(PAGE_KEYS).map(pageShortcuts)

const current = computed(() => pages.find(page => page.name === (route.params.page || 'index')) || pages[0])
const position = computed(() => pages.indexOf(current.value))
const previous = computed(() => pages[position.value - 1] || null)
const next = computed(() => pages[position.value + 1] || null)

const groups = computed(() => {
  const byName = new Map()
  for (const shortcut of SHORTCUTS) {
    if (!byName.has(shortcut.group)) byName.set(shortcut.group, { name: shortcut.group, entries: [] })
    byName.get(shortcut.group).entries.push(shortcut)
  }
  return [...byName.values()]
})

/** The anchor of a heading: lowercase, hyphens, no emoji. */
function slug(text) {
  return String(text)
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .trim()
    .replace(/\s+/g, '-')
}

const renderer = new marked.Renderer()
renderer.heading = (text, level) => `<h${level} id="${slug(text)}">${text}</h${level}>\n`
const html = computed(() => marked.parse(markdown(current.value.name), { renderer, gfm: true, breaks: false }))

function open(name) {
  router.push(name === 'index' ? { name: 'help' } : { name: 'help-page', params: { page: name } })
}

function jump(id) {
  article.value?.querySelector(`#${CSS.escape(id)}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/** Links in a page: its anchors scroll, its sibling pages open here, everything else outside. */
function follow(event) {
  const anchor = event.target?.closest?.('a[href]')
  if (!anchor) return
  event.preventDefault()
  const target = helpTarget(anchor.getAttribute('href') || '')
  if (target.kind === 'anchor') jump(target.id)
  else if (target.kind === 'page') {
    open(target.name)
    if (target.id) nextTick(() => jump(target.id))
  } else if (target.url) openExternal(target.url)
}

watch(() => route.params.page, () => window.scrollTo({ top: 0 }))
</script>
