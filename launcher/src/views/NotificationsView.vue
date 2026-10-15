<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Notifications</h1>
        <p class="mt-1 text-xs text-gray-500">
          Everything the launcher has said since it was opened. Archiving puts an entry away without losing it.
        </p>
      </div>
      <segmented-control v-model="tab" :options="tabs" class="ml-auto shrink-0" />
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <button
        v-if="tab === 'inbox' && inbox.length"
        type="button"
        class="lx-action"
        @click="archiveAll"
      >
        <Archive class="w-3.5 h-3.5" /> Archive all
      </button>
      <button
        v-if="tab === 'archived' && archived.length"
        type="button"
        class="lx-action is-danger"
        @click="clearArchived"
      >
        <Trash2 class="w-3.5 h-3.5" /> Delete archived
      </button>
    </div>

    <p v-if="!shown.length" class="bm-card p-5 text-xs text-gray-500">
      {{ tab === 'inbox' ? 'Nothing new.' : 'Nothing archived.' }}
    </p>

    <div v-else class="lx-list bg-white">
      <article
        v-for="entry in shown"
        :key="entry.id"
        class="lx-notice lx-notice-page"
        :class="{ 'is-error': entry.kind === 'error' }"
      >
        <span class="lx-notice-time">{{ time(entry.at) }}</span>
        <component
          :is="entry.link ? 'router-link' : 'span'"
          :to="entry.link || undefined"
          class="lx-notice-text"
          :class="{ 'is-link': entry.link }"
          :title="entry.link ? `Go to ${sectionTitle(entry.link)}` : undefined"
        >{{ entry.text }}</component>
        <span class="flex items-center gap-1 shrink-0">
          <button
            v-if="!entry.archived"
            type="button"
            class="lx-action"
            title="Archive"
            @click="archiveNotification(entry.id)"
          >
            <Archive class="w-3.5 h-3.5" />
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
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Archive, ArchiveRestore, Trash2, X } from 'lucide-vue-next'
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

const tab = ref('inbox')
const inbox = computed(() => state.notifications.filter(entry => !entry.archived))
const archived = computed(() => state.notifications.filter(entry => entry.archived))
const shown = computed(() => (tab.value === 'inbox' ? inbox.value : archived.value))
const tabs = computed(() => [
  { value: 'inbox', label: `Inbox (${inbox.value.length})` },
  { value: 'archived', label: `Archived (${archived.value.length})` }
])

function time(at) {
  return new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function sectionTitle(link) {
  return sections.find(section => section.name === link?.name)?.title || 'the section'
}
</script>
