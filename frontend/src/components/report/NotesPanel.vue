<template>
  <details class="bm-card border border-gray-100 p-4" @toggle="toggle($event.target.open)">
    <summary class="cursor-pointer text-sm font-semibold text-gray-700">
      {{ title }} <span class="text-xs text-gray-400">({{ notes.length }})</span>
    </summary>
    <div class="mt-4 space-y-4">
      <p v-if="loading" class="text-xs text-gray-500" role="status">Loading comments...</p>
      <p v-if="error" class="text-xs text-red-700" role="alert">
        {{ error }}
        <button v-if="!saving" type="button" class="underline cursor-pointer ml-2" @click="loadNotes">Reload comments</button>
      </p>
      <ol v-if="notes.length" class="space-y-3">
        <li v-for="(note, index) in notes" :key="index" class="rounded-xl bg-gray-50 p-3">
          <div class="flex flex-wrap gap-2 text-xs text-gray-500 mb-2">
            <span v-if="note.author" class="font-semibold text-gray-700">{{ note.author }}</span>
            <time v-if="note.timestamp" :datetime="note.timestamp">{{ formatTimestamp(note.timestamp) }}</time>
          </div>
          <p class="text-sm text-gray-800 whitespace-pre-wrap break-words">{{ note.content }}</p>
        </li>
      </ol>
      <p v-else-if="!loading" class="text-xs text-gray-400">No comments yet.</p>
      <form v-if="canEdit" class="no-print space-y-2" @submit.prevent="addComment">
        <label class="block text-xs font-semibold text-gray-600">
          Add a comment
          <textarea
            v-model="draft"
            rows="3"
            :disabled="saving"
            class="mt-2 block w-full rounded-lg border border-gray-200 p-3 text-sm font-normal text-gray-800"
            placeholder="Write a comment..."
          ></textarea>
        </label>
        <div class="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            :disabled="saving || !draft.trim() || !reportId"
            class="bm-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >{{ saving ? 'Adding...' : 'Add comment' }}</button>
          <span class="text-xs text-gray-400">Comments are permanent and cannot be edited or deleted.</span>
        </div>
      </form>
    </div>
  </details>
</template>

<script setup>
import { canEdit } from '../../store.js'
import { useNotes } from '../../composables/useNotes.js'

const props = defineProps({
  reportId: { type: String, required: true },
  protocolId: { type: String, default: null },
  notes: { type: Array, default: () => [] },
  title: { type: String, default: 'Comments' }
})
const emit = defineEmits(['update:notes'])
const { notes, draft, loading, saving, error, loadNotes, addComment, toggle } = useNotes(props, emit)

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString()
}
</script>
