<!--
  The count of what was said, and the bubble it opens.

  The same bell serves the status bar — a small pill, the bubble opening
  upward — and the toolbars of the dashboard's inner pages — a control
  among controls, the bubble opening downward. The bubble shows the five
  most recent entries of the last day, each the way to its section, and
  leads to the Notifications page for the rest. Links are plain addresses,
  so they work from the launcher page and from the dashboard page alike.
-->
<template>
  <div ref="corner" class="relative inline-flex items-center">
    <button
      v-if="inbox.length"
      type="button"
      :class="[toolbar ? 'lx-bell' : 'lx-count', { 'is-open': open }]"
      :title="`${inbox.length} notification${inbox.length === 1 ? '' : 's'}`"
      :aria-expanded="open"
      @click="open = !open"
    >
      <Bell :class="toolbar ? 'w-3.5 h-3.5' : 'w-3 h-3'" />
      <span class="lx-count-badge">{{ inbox.length }}</span>
    </button>

    <div v-if="open && inbox.length" class="lx-notices" :class="{ 'is-below': toolbar }" role="list">
      <div class="lx-notices-head">
        <a :href="launcherHref({ name: 'notifications' })" class="hover:text-[#3b107e] transition" title="All notifications" @click="open = false">
          Notifications
        </a>
        <button type="button" class="hover:text-[#3b107e] transition" title="Archive all" @click="archiveEverything">Archive all</button>
      </div>
      <div
        v-for="entry in recent"
        :key="entry.id"
        class="lx-notice"
        :class="{ 'is-error': entry.kind === 'error' }"
        role="listitem"
      >
        <span class="lx-notice-time">{{ time(entry.at) }}</span>
        <component
          :is="entry.link ? 'a' : 'span'"
          :href="entry.link ? launcherHref(entry.link) : undefined"
          class="lx-notice-text"
          :class="{ 'is-link': entry.link }"
          :title="entry.link ? `Go to ${sectionTitle(entry.link)}` : undefined"
          @click="entry.link && (open = false)"
        >{{ entry.text }}</component>
        <button type="button" class="lx-notice-close" :aria-label="`Archive: ${entry.text}`" title="Archive" @click="archiveNotification(entry.id)">
          <X class="w-3 h-3" />
        </button>
      </div>
      <a v-if="inbox.length > recent.length" :href="launcherHref({ name: 'notifications' })" class="lx-notices-more" @click="open = false">
        {{ recent.length ? `${inbox.length - recent.length} more…` : `${inbox.length} older…` }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Bell, X } from 'lucide-vue-next'
import { sections } from '../router.js'
import { archiveAll, archiveNotification, inbox } from '../state.js'
import { launcherHref } from '../lib/links.js'
import { isRecent } from '../lib/time.js'

defineProps({
  /** Drawn as a toolbar control, the bubble below it; otherwise the status bar pill. */
  toolbar: { type: Boolean, default: false }
})

/** How many entries the bubble shows; the page has them all. */
const RECENT = 5

const open = ref(false)
const corner = ref(null)
const now = ref(Date.now())

/** The five most recent of the last day; the page has the rest. */
const recent = computed(() => inbox.value.filter(entry => isRecent(entry.at, now.value)).slice(0, RECENT))

function sectionTitle(link) {
  return sections.find(section => section.name === link?.name)?.title || 'the section'
}

function time(at) {
  return new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function archiveEverything() {
  archiveAll()
  open.value = false
}

/** A click anywhere else, the window losing focus, or a navigation closes the list. */
function closeFromOutside(event) {
  if (!open.value) return
  if (event?.type === 'pointerdown' && corner.value?.contains(event.target)) return
  open.value = false
}

watch(open, opened => {
  if (opened) now.value = Date.now()
})
watch(() => inbox.value.length, count => {
  if (!count) open.value = false
})

onMounted(() => {
  document.addEventListener('pointerdown', closeFromOutside)
  window.addEventListener('blur', closeFromOutside)
  window.addEventListener('hashchange', closeFromOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', closeFromOutside)
  window.removeEventListener('blur', closeFromOutside)
  window.removeEventListener('hashchange', closeFromOutside)
})
</script>
