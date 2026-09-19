<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-5xl w-full p-6 shadow-2xl border border-gray-100 flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-4 border-b border-gray-100 shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-gray-900 leading-tight">
                {{ archive?.name || 'Archive Content' }}
              </h2>
              <span class="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                {{ archive?.report_count }} reports
              </span>
              <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                {{ formatBytes(archive?.size_bytes || 0) }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">
              Peaking into archive index without unzipping archive file
            </p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 text-lg transition cursor-pointer"
        >
          &times;
        </button>
      </div>

      <!-- Description & Filters Summary -->
      <div v-if="archive?.description || hasFilters" class="py-2.5 px-3 my-3 bg-slate-50 rounded-xl border border-slate-200/70 text-xs shrink-0 space-y-1.5">
        <p v-if="archive?.description" class="text-gray-700 italic">
          "{{ archive.description }}"
        </p>
        <div v-if="hasFilters" class="flex flex-wrap items-center gap-1.5 text-[11px]">
          <span class="text-gray-400 font-semibold">Captured Filters:</span>
          <span v-if="archive.filters?.search" class="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
            query: "{{ archive.filters.search }}"
          </span>
          <span v-if="archive.filters?.subfolder" class="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
            folder: {{ archive.filters.subfolder }}
          </span>
          <span v-for="tag in archive.filters?.tags || []" :key="'tag-' + tag" class="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-mono">
            tag:{{ tag }}
          </span>
          <span v-for="proto in archive.filters?.protocols || []" :key="'proto-' + proto" class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono">
            {{ proto }}
          </span>
          <span v-for="plat in archive.filters?.platforms || []" :key="'plat-' + plat" class="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">
            platform:{{ plat }}
          </span>
          <span v-for="auth in archive.filters?.authors || []" :key="'auth-' + auth" class="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">
            author:{{ auth }}
          </span>
        </div>
      </div>

      <!-- Search inside peaked reports & selection count -->
      <div class="flex items-center justify-between gap-3 my-2 shrink-0">
        <div class="relative flex-1 max-w-sm">
          <svg class="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filter indexed reports..."
            class="w-full pl-8 pr-3 py-1.5 text-xs bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
          />
        </div>

        <div class="flex items-center gap-2 text-xs text-gray-600">
          <span v-if="selectedIds.length > 0" class="font-semibold text-indigo-600">
            {{ selectedIds.length }} of {{ reports.length }} selected
          </span>
          <button
            type="button"
            @click="toggleSelectAll"
            class="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-gray-200 hover:bg-gray-100 transition cursor-pointer"
          >
            {{ allSelected ? 'Deselect All' : 'Select All' }}
          </button>
        </div>
      </div>

      <!-- Reports Table (Scrollable) -->
      <div class="flex-1 min-h-0 overflow-y-auto border border-gray-100 rounded-xl">
        <div v-if="loading" class="p-12 text-center text-xs text-gray-500 flex flex-col items-center justify-center gap-2">
          <div class="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          Reading archive index...
        </div>

        <div v-else-if="error" class="p-8 text-center text-xs text-red-600">
          Failed to load archive index: {{ error }}
        </div>

        <div v-else-if="filteredReports.length === 0" class="p-12 text-center text-xs text-gray-400">
          No reports match your search query.
        </div>

        <table v-else class="w-full text-left border-collapse text-xs">
          <thead class="bg-gray-50 text-gray-500 uppercase tracking-wider text-[10px] sticky top-0 z-10 border-b border-gray-200/80">
            <tr>
              <th class="py-2 px-3 w-8 text-center">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  class="rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </th>
              <th class="py-2 px-3">Report ID / Title</th>
              <th class="py-2 px-3">Date & Time</th>
              <th class="py-2 px-3">Author</th>
              <th class="py-2 px-3">Platform</th>
              <th class="py-2 px-3">Protocols</th>
              <th class="py-2 px-3">Qubits</th>
              <th class="py-2 px-3">Tags</th>
              <th class="py-2 px-3 text-right">Size</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="rep in filteredReports"
              :key="rep.id"
              class="hover:bg-indigo-50/40 transition-colors"
              :class="{ 'bg-indigo-50/20': isSelected(rep.id) }"
            >
              <td class="py-2 px-3 text-center">
                <input
                  type="checkbox"
                  :checked="isSelected(rep.id)"
                  @change="toggleSelect(rep.id)"
                  class="rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </td>
              <td class="py-2 px-3">
                <div class="font-medium text-gray-900 font-mono text-[11px]">
                  {{ rep.id }}
                </div>
                <div v-if="rep.title && rep.title !== rep.id" class="text-[11px] text-gray-500">
                  {{ rep.title }}
                </div>
              </td>
              <td class="py-2 px-3 text-gray-600 whitespace-nowrap">
                <div>{{ rep.date }}</div>
                <div v-if="rep.time" class="text-[10px] text-gray-400">{{ rep.time }}</div>
              </td>
              <td class="py-2 px-3 text-gray-700">
                <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-medium">
                  {{ rep.author || 'Unknown' }}
                </span>
              </td>
              <td class="py-2 px-3 text-gray-600">
                {{ rep.platform || '—' }}
              </td>
              <td class="py-2 px-3">
                <div class="flex flex-wrap gap-1 max-w-xs">
                  <span
                    v-for="p in (rep.protocols || []).slice(0, 3)"
                    :key="p"
                    class="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono text-[10px]"
                  >
                    {{ p }}
                  </span>
                  <span
                    v-if="(rep.protocols || []).length > 3"
                    class="text-[10px] text-gray-400 self-center"
                  >
                    +{{ rep.protocols.length - 3 }}
                  </span>
                </div>
              </td>
              <td class="py-2 px-3 text-gray-600 font-mono text-[11px]">
                <span v-if="rep.qubits && rep.qubits.length">
                  {{ rep.qubits.slice(0, 4).join(', ') }}{{ rep.qubits.length > 4 ? '…' : '' }}
                </span>
                <span v-else class="text-gray-400">—</span>
              </td>
              <td class="py-2 px-3">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="t in (rep.tags || [])"
                    :key="t"
                    class="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-mono text-[10px]"
                  >
                    {{ t }}
                  </span>
                </div>
              </td>
              <td class="py-2 px-3 text-right text-gray-500 font-mono whitespace-nowrap text-[11px]">
                {{ formatBytes(rep.size_bytes || 0) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer Actions -->
      <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between shrink-0">
        <div class="text-xs text-gray-500">
          Showing {{ filteredReports.length }} report(s)
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="$emit('close')"
            class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
          >
            Close
          </button>

          <!-- Restore Selected -->
          <button
            v-if="selectedIds.length > 0"
            @click="$emit('restore-selected', selectedIds)"
            class="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition cursor-pointer flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Restore Selected ({{ selectedIds.length }})
          </button>

          <!-- Restore All -->
          <button
            @click="$emit('restore-all')"
            class="px-4 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition cursor-pointer flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Restore All Reports
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { apiFetch } from '../../store.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  archive: { type: Object, default: null }
})

defineEmits(['close', 'restore-selected', 'restore-all'])

const reports = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const selectedIds = ref([])

const hasFilters = computed(() => {
  const f = props.archive?.filters || {}
  return Boolean(
    f.search ||
    f.subfolder ||
    (f.tags && f.tags.length > 0) ||
    (f.protocols && f.protocols.length > 0) ||
    (f.platforms && f.platforms.length > 0) ||
    (f.authors && f.authors.length > 0)
  )
})

const filteredReports = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return reports.value
  return reports.value.filter(r => {
    const hay = [
      r.id,
      r.title,
      r.author,
      r.platform,
      ...(r.protocols || []),
      ...(r.qubits || []),
      ...(r.tags || [])
    ].join(' ').toLowerCase()
    return hay.includes(q)
  })
})

const allSelected = computed(() => {
  return (
    filteredReports.value.length > 0 &&
    filteredReports.value.every(r => selectedIds.value.includes(r.id))
  )
})

function isSelected(id) {
  return selectedIds.value.includes(id)
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

function toggleSelectAll() {
  if (allSelected.value) {
    const cur = new Set(filteredReports.value.map(r => r.id))
    selectedIds.value = selectedIds.value.filter(id => !cur.has(id))
  } else {
    const all = new Set([...selectedIds.value, ...filteredReports.value.map(r => r.id)])
    selectedIds.value = Array.from(all)
  }
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function loadIndex() {
  if (!props.archive?.id) return
  loading.value = true
  error.value = null
  selectedIds.value = []
  searchQuery.value = ''
  try {
    const res = await apiFetch(`/api/archives/${encodeURIComponent(props.archive.id)}/index`)
    if (!res.ok) {
      throw new Error(`Failed to load index (${res.status})`)
    }
    reports.value = await res.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.show, props.archive?.id],
  ([show, id]) => {
    if (show && id) {
      loadIndex()
    } else {
      reports.value = []
    }
  }
)
</script>
