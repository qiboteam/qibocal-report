<!--
  Every notification, arranged as an inbox: grouped by the section it is
  about, as GitHub groups its notifications by repository, each group with a
  heading that leads to the section and a way to put the whole group away.
  The rows read like the rest of the application — the same text, the same
  size — with the time as a distance from now, and the actions on the right.
-->
<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Notifications</h1>
        <p class="mt-1 text-xs text-gray-500">
          Everything the launcher has said since it was opened. Marking an entry done puts it away without losing it.
        </p>
      </div>
      <segmented-control v-model="tab" :options="tabs" class="ml-auto shrink-0" />
    </div>

    <p v-if="!groups.length" class="bm-card p-6 text-center text-xs text-gray-500">
      {{ tab === 'inbox' ? 'All caught up: nothing new.' : 'Nothing has been marked done.' }}
    </p>

    <section v-for="group in groups" :key="group.key" class="bm-card overflow-hidden">
      <header class="flex items-center gap-3 px-4 py-2.5 border-b border-gray-100 bg-[#fafafa]">
        <component
          :is="group.link ? 'router-link' : 'span'"
          :to="group.link || undefined"
          class="text-xs font-semibold text-gray-700"
          :class="{ 'hover:text-[#3b107e] transition': group.link }"
        >
          {{ group.title }}
        </component>
        <span class="text-[11px] text-gray-400">{{ group.entries.length }}</span>
        <button
          v-if="tab === 'inbox'"
          type="button"
          class="lx-action ml-auto"
          :title="`Mark everything about ${group.title} done`"
          @click="group.entries.forEach(entry => archiveNotification(entry.id))"
        >
          <Check class="w-3.5 h-3.5" /> Done
        </button>
        <button
          v-else
          type="button"
          class="lx-action ml-auto"
          :title="`Bring everything about ${group.title} back`"
          @click="group.entries.forEach(entry => unarchiveNotification(entry.id))"
        >
          <ArchiveRestore class="w-3.5 h-3.5" /> Back to inbox
        </button>
      </header>

      <article
        v-for="entry in group.entries"
        :key="entry.id"
        class="lx-inbox-row"
        :class="{ 'is-error': entry.kind === 'error' }"
      >
        <component :is="entry.kind === 'error' ? AlertTriangle : Info" class="lx-inbox-icon w-3.5 h-3.5" />
        <component
          :is="entry.link ? 'router-link' : 'span'"
          :to="entry.link || undefined"
          class="lx-inbox-text"
          :class="{ 'is-link': entry.link }"
          :title="entry.link ? `Go to ${group.title}` : undefined"
        >{{ entry.text }}</component>
        <span class="lx-inbox-time" :title="new Date(entry.at).toLocaleString()">{{ timeAgo(entry.at, now) }}</span>
        <span class="lx-inbox-actions">
          <button
            v-if="!entry.archived"
            type="button"
            class="lx-action"
            title="Done"
            @click="archiveNotification(entry.id)"
          >
            <Check class="w-3.5 h-3.5" />
          </button>
          <button
            v-else
            type="button"
            class="lx-action"
            title="Back to the inbox"
            @click="unarchiveNotification(entry.id)"
          >
            <ArchiveRestore class="w-3.5 h-3.5" />
          </button>
          <button type="button" class="lx-action is-danger" title="Delete" @click="dismissNotification(entry.id)">
            <X class="w-3.5 h-3.5" />
          </button>
        </span>
      </article>
    </section>

    <div v-if="groups.length" class="flex items-center gap-2">
      <button v-if="tab === 'inbox'" type="button" class="lx-action" @click="archiveAll">
        <Check class="w-3.5 h-3.5" /> Mark all done
      </button>
      <button v-else type="button" class="lx-action is-danger" @click="clearArchived">
        <Trash2 class="w-3.5 h-3.5" /> Delete everything done
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { AlertTriangle, ArchiveRestore, Check, Info, Trash2, X } from 'lucide-vue-next'
import SegmentedControl from '../components/SegmentedControl.vue'
import { sections } from '../router.js'
import {
  state,
  archiveNotification,
  archiveAll,
  clearArchived,
  dismissNotification,
  unarchiveNotification
} from '../state.js'
import { timeAgo } from '../lib/time.js'

const tab = ref('inbox')
/** Re-read once a minute, so "5 minutes ago" keeps being true. */
const now = ref(Date.now())
let ticker = null

const inbox = computed(() => state.notifications.filter(entry => !entry.archived))
const done = computed(() => state.notifications.filter(entry => entry.archived))
const shown = computed(() => (tab.value === 'inbox' ? inbox.value : done.value))
const tabs = computed(() => [
  { value: 'inbox', label: `Inbox (${inbox.value.length})` },
  { value: 'done', label: `Done (${done.value.length})` }
])

/** The entries by the section they are about, newest group first. */
const groups = computed(() => {
  const byKey = new Map()
  for (const entry of shown.value) {
    const section = sections.find(item => item.name === entry.link?.name)
    const key = section?.name || 'general'
    if (!byKey.has(key)) {
      byKey.set(key, {
        key,
        title: section?.title || 'General',
        link: section ? { name: section.name } : null,
        entries: []
      })
    }
    byKey.get(key).entries.push(entry)
  }
  return [...byKey.values()].sort((left, right) => right.entries[0].at - left.entries[0].at)
})

onMounted(() => {
  ticker = setInterval(() => { now.value = Date.now() }, 60_000)
})
onBeforeUnmount(() => clearInterval(ticker))
</script>
