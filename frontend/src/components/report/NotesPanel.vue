<!--
  The comments of a report, or of a protocol: a thread folded under one line,
  the way the rest of a card reads — small text, the time as a distance from
  now, the author in bold where there is one. Comments are Markdown. Each
  may be changed or removed by whoever wrote it, or by an administrator; the
  controls appear on hover, at the end of the line.
-->
<template>
  <details class="notes group/notes" @toggle="toggle($event.target.open)">
    <summary class="flex items-center gap-1.5 cursor-pointer select-none text-xs text-gray-500 hover:text-gray-800 transition py-1 list-none [&::-webkit-details-marker]:hidden">
      <svg class="w-3 h-3 transition-transform group-open/notes:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      <span class="font-semibold">{{ title }}</span>
      <span class="text-gray-400">{{ notes.length }}</span>
      <span v-if="latest" class="text-gray-400 truncate hidden sm:inline">· last {{ timeAgo(latest.timestamp, now) }}</span>
    </summary>

    <div class="mt-1.5 pl-4.5 space-y-2">
      <p v-if="loading && !notes.length" class="text-xs text-gray-400" role="status">Loading…</p>
      <p v-if="error" class="text-xs text-red-700" role="alert">
        {{ error }}
        <button v-if="!saving" type="button" class="font-semibold cursor-pointer ml-1 hover:text-red-900 transition" @click="loadNotes">Reload</button>
      </p>

      <ol v-if="notes.length" class="divide-y divide-gray-100">
        <li v-for="(note, index) in notes" :key="`${note.timestamp}-${index}`" class="group/note py-1.5">
          <div class="flex items-baseline gap-2 text-[11px] text-gray-400">
            <span v-if="note.author" class="font-semibold text-gray-700">{{ note.author }}</span>
            <time v-if="note.timestamp" :datetime="note.timestamp" :title="new Date(note.timestamp).toLocaleString()">{{ timeAgo(note.timestamp, now) }}</time>
            <span v-if="canChange(note) && editing !== index" class="no-print ml-auto flex items-center gap-1 opacity-0 group-hover/note:opacity-100 focus-within:opacity-100 transition">
              <button type="button" class="p-0.5 rounded hover:text-[#833dff] hover:bg-purple-50 cursor-pointer" title="Edit" :disabled="saving" @click="startEdit(index)">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
              </button>
              <button type="button" class="p-0.5 rounded hover:text-red-600 hover:bg-red-50 cursor-pointer" title="Remove" :disabled="saving" @click="confirmRemove(index)">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            </span>
          </div>

          <!-- Changing it: the text in place, Markdown as when it was written. -->
          <form v-if="editing === index" class="no-print mt-1 space-y-1.5" @submit.prevent="saveEdit">
            <textarea
              v-model="editDraft"
              rows="3"
              :disabled="saving"
              class="block w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs text-gray-800 font-mono focus:outline-none focus:ring-2 focus:ring-[#833dff]/40"
              @keydown.esc.prevent="cancelEdit"
              @keydown.meta.enter.prevent="saveEdit"
              @keydown.ctrl.enter.prevent="saveEdit"
            ></textarea>
            <div class="flex items-center gap-2">
              <button type="submit" :disabled="saving || !editDraft.trim()" class="bm-btn-primary rounded-lg px-2.5 py-1 text-[11px] font-semibold cursor-pointer disabled:opacity-40">{{ saving ? 'Saving…' : 'Save' }}</button>
              <button type="button" :disabled="saving" class="text-[11px] text-gray-500 hover:text-gray-800 cursor-pointer" @click="cancelEdit">Cancel</button>
            </div>
          </form>
          <div v-else class="notes-body text-xs text-gray-800 break-words" v-html="renderMarkdown(note.content)"></div>
        </li>
      </ol>
      <p v-else-if="!loading" class="text-xs text-gray-400">No comments yet.</p>

      <!-- A new comment: one small field, Markdown, Cmd/Ctrl+Enter sends it. -->
      <form v-if="canEdit && editing === null" class="no-print flex items-start gap-2 pt-1" @submit.prevent="addComment">
        <textarea
          v-model="draft"
          rows="1"
          :disabled="saving"
          class="block flex-1 min-w-0 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#833dff]/40 resize-y"
          :class="{ 'font-mono': draft.includes('`') }"
          placeholder="Add a comment… Markdown is fine"
          aria-label="Add a comment"
          @focus="$event.target.rows = 3"
          @blur="!draft && ($event.target.rows = 1)"
          @keydown.meta.enter.prevent="addComment"
          @keydown.ctrl.enter.prevent="addComment"
        ></textarea>
        <button
          type="submit"
          :disabled="saving || !draft.trim() || !reportId"
          class="bm-btn-primary rounded-lg px-2.5 py-1.5 text-[11px] font-semibold cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          title="Add the comment (Cmd/Ctrl+Enter)"
        >{{ saving ? 'Adding…' : 'Add' }}</button>
      </form>
    </div>
  </details>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { canEdit } from '../../store.js'
import { useNotes } from '../../composables/useNotes.js'
import { renderMarkdown, timeAgo } from '../../utils/markdown.js'

const props = defineProps({
  reportId: { type: String, required: true },
  protocolId: { type: String, default: null },
  notes: { type: Array, default: () => [] },
  title: { type: String, default: 'Comments' }
})
const emit = defineEmits(['update:notes'])
const {
  notes, draft, loading, saving, error, editing, editDraft, canChange,
  loadNotes, addComment, startEdit, cancelEdit, saveEdit, removeComment, toggle
} = useNotes(props, emit)

const latest = computed(() => notes.value[notes.value.length - 1] || null)

/** Re-read once a minute, so "5 minutes ago" keeps being true. */
const now = ref(Date.now())
let ticker = null
onMounted(() => { ticker = setInterval(() => { now.value = Date.now() }, 60_000) })
onBeforeUnmount(() => clearInterval(ticker))

function confirmRemove(index) {
  if (window.confirm('Remove this comment? It is gone for everyone.')) removeComment(index)
}
</script>

<style scoped>
/* Comments are Markdown: the few elements they use, in the card's own scale. */
.notes-body :deep(p) { margin: 0 0 0.35rem; }
.notes-body :deep(p:last-child) { margin-bottom: 0; }
.notes-body :deep(ul), .notes-body :deep(ol) { margin: 0.2rem 0 0.35rem; padding-left: 1.25rem; }
.notes-body :deep(ul) { list-style: disc; }
.notes-body :deep(ol) { list-style: decimal; }
.notes-body :deep(code) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.92em; background: #f3f0fa; border-radius: 4px; padding: 0 0.3em; }
.notes-body :deep(pre) { background: #f3f0fa; border-radius: 8px; padding: 0.5rem 0.65rem; overflow-x: auto; margin: 0.3rem 0; }
.notes-body :deep(pre code) { background: transparent; padding: 0; }
.notes-body :deep(a) { color: #833dff; }
.notes-body :deep(a:hover) { color: #3b107e; }
.notes-body :deep(blockquote) { border-left: 2px solid #ddd0ff; padding-left: 0.6rem; color: #6b7280; margin: 0.3rem 0; }
.notes-body :deep(h1), .notes-body :deep(h2), .notes-body :deep(h3) { font-size: 0.85rem; font-weight: 600; margin: 0.4rem 0 0.2rem; font-family: inherit; }
.notes-body :deep(table) { border-collapse: collapse; font-size: 0.95em; margin: 0.3rem 0; }
.notes-body :deep(th), .notes-body :deep(td) { border: 1px solid #e5e7eb; padding: 0.15rem 0.45rem; }
</style>
