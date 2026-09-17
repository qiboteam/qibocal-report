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
          v-for="t in (report.tags || report.labels || [])"
          :key="t"
          @click.stop="onTagClick(t)"
          class="group/tag inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 hover:text-purple-900 font-mono cursor-pointer transition select-none"
          :title="`Filter by tag: ${t}`"
        >
          <span>{{ t }}</span>
          <button
            type="button"
            @click.stop="$emit('remove-tag', t)"
            class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-red-600 font-bold transition text-[11px] leading-none opacity-60 hover:opacity-100 cursor-pointer shrink-0 ml-0.5"
            title="Remove tag"
          >
            &times;
          </button>
        </span>
        <span
          v-if="report.has_cached_report"
          class="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase bg-emerald-100 text-emerald-800"
        >
          Pre-cached
        </span>
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
              @click="startEditAuthor"
              class="text-gray-400 hover:text-[#833dff] transition cursor-pointer"
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
              class="px-1.5 py-0.5 text-xs border border-purple-300 rounded focus:outline-none focus:ring-1 focus:ring-[#833dff] w-28 font-medium"
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

    <!-- Tags & Git Commit -->
    <div
      v-if="(report.tags || report.labels)?.length || report.history?.git_commit"
      class="mt-4 pt-3 border-t border-gray-50 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500"
    >
      <div class="flex items-center gap-1.5 flex-wrap">
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
            type="button"
            @click.stop="$emit('remove-tag', l)"
            class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-red-600 font-bold transition text-[11px] leading-none opacity-60 hover:opacity-100 cursor-pointer shrink-0 ml-0.5"
            title="Remove tag"
          >
            &times;
          </button>
        </span>
      </div>
      <div v-if="report.history?.git_commit" class="font-mono text-[11px] text-gray-400">
        commit: {{ report.history.git_commit }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

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
