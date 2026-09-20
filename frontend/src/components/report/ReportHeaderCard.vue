<template>
  <div class="bm-card p-6 border border-gray-100">
    <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-gray-100">
      <div>
        <h1 class="text-xl sm:text-2xl font-bold font-mono text-gray-900">
          {{ report.id }}
        </h1>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
          {{ report.platform }}
        </span>
        <span
          v-if="report.has_cached_report"
          class="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase bg-emerald-100 text-emerald-800"
        >
          Pre-cached
        </span>

        <a
          href="https://qibo.science/qibocal/stable/protocols/"
          target="_blank"
          rel="noopener noreferrer"
          class="no-print px-2.5 py-1 rounded-full text-xs font-semibold bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs inline-flex items-center gap-1.5 transition cursor-pointer"
          title="Open Qibocal Protocols Documentation"
        >
          <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <span>Qibocal Docs</span>
          <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>

    <!-- Metadata Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 text-xs">
      <div>
        <span class="text-gray-400 block mb-0.5">Author</span>
        <div class="flex items-center gap-1.5">
          <template v-if="!isEditingAuthor">
            <strong class="text-gray-800">{{ report.author }}</strong>
            <button
              v-if="!isViewer"
              @click="startEditAuthor"
              class="no-print text-gray-400 hover:text-[#833dff] transition cursor-pointer"
              title="Edit author"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          </template>
          <template v-else>
            <input
              v-model="editAuthorText"
              type="text"
              class="px-2 py-0.5 text-xs bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400/50 w-28 font-medium text-gray-800"
              @keyup.enter="onSaveAuthor"
              @keyup.esc="isEditingAuthor = false"
            />
            <button
              @click="onSaveAuthor"
              :disabled="savingAuthor"
              class="text-emerald-600 hover:text-emerald-700 font-bold text-xs cursor-pointer"
              title="Save"
            >
              ✓
            </button>
            <button
              @click="isEditingAuthor = false"
              class="text-gray-400 hover:text-gray-600 font-bold text-xs cursor-pointer"
              title="Cancel"
            >
              ✕
            </button>
          </template>
        </div>
      </div>
      <div>
        <span class="text-gray-400 block mb-0.5">Execution Date</span>
        <strong class="text-gray-800 font-mono">{{ report.date }} {{ report.time }}</strong>
      </div>
      <div>
        <span class="text-gray-400 block mb-0.5">Total Duration</span>
        <strong class="text-gray-800 font-mono">{{ report.total_execution_time || 'N/A' }}</strong>
      </div>
      <div>
        <span class="text-gray-400 block mb-0.5">Target Qubits</span>
        <strong class="text-gray-800 font-mono">Q{{ report.targets.join(', Q') }}</strong>
      </div>
    </div>

    <!-- Platform Navigation Buttons (below metadata) -->
    <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-xs font-semibold text-gray-500">Platform Files:</span>

        <!-- Old Platform Button -->
        <button
          type="button"
          @click="goToPlatform('old')"
          class="no-print px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs inline-flex items-center gap-1.5 transition cursor-pointer"
          title="Open Old Platform navigation (parameters.json & calibration.json)"
        >
          <svg class="w-3.5 h-3.5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span>Old Platform</span>
        </button>

        <!-- New Platform Button -->
        <button
          type="button"
          @click="goToPlatform('new')"
          class="no-print px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50 hover:bg-purple-100 text-[#833dff] hover:text-purple-900 border border-purple-200 hover:border-purple-300 shadow-2xs inline-flex items-center gap-1.5 transition cursor-pointer"
          title="Open New Platform navigation (parameters.json & calibration.json)"
        >
          <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
          <span>New Platform</span>
        </button>
      </div>

      <div v-if="report.history?.git_commit" class="font-mono text-[11px] text-gray-400">
        commit: {{ report.history.git_commit }}
      </div>
    </div>

    <!-- Tags -->
    <div
      v-if="(report.tags || report.labels)?.length"
      class="mt-3 pt-2.5 border-t border-gray-50 flex items-center gap-1.5 flex-wrap text-xs text-gray-500"
    >
      <span class="text-gray-500 font-semibold">Tags:</span>
      <span
        v-for="l in (report.tags || report.labels || [])"
        :key="l"
        @click.stop="onTagClick(l)"
        class="group/tag inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 hover:text-purple-900 font-mono cursor-pointer transition select-none"
        :title="`Filter by tag: ${l}`"
      >
        <span>{{ l }}</span>
        <button
          v-if="!isViewer"
          type="button"
          @click.stop="$emit('remove-tag', l)"
          class="no-print bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-red-600 font-bold transition text-[11px] leading-none opacity-60 hover:opacity-100 cursor-pointer shrink-0 ml-0.5"
          title="Remove tag"
        >
          &times;
        </button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { isViewer } from '../../store.js'

const props = defineProps({
  report: { type: Object, required: true },
  savingAuthor: { type: Boolean, default: false }
})

const emit = defineEmits(['remove-tag', 'save-author'])
const router = useRouter()

function onTagClick(tag) {
  if (tag) {
    router.push({ path: '/dashboard', query: { label: tag } })
  }
}

function goToPlatform(type) {
  router.push({
    name: 'platform',
    params: { id: props.report.id },
    query: { type }
  })
}

const isEditingAuthor = ref(false)
const editAuthorText = ref('')

function startEditAuthor() {
  editAuthorText.value = props.report?.author === 'Unknown' ? '' : (props.report?.author || '')
  isEditingAuthor.value = true
}

async function onSaveAuthor() {
  emit('save-author', {
    author: editAuthorText.value.trim(),
    onComplete: () => {
      isEditingAuthor.value = false
    }
  })
}
</script>
