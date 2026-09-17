<template>
  <div v-if="!isCollapsed">
    <!-- Expanded Protocol Summary -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Protocols Summary</span>
      <span class="text-[11px] text-purple-700 font-mono bg-purple-100 px-1.5 py-0.5 rounded">
        {{ protocols?.length || 0 }} routines
      </span>
    </div>

    <div class="space-y-1.5">
      <a
        v-for="p in protocols"
        :key="p.id"
        @click.prevent="scrollToProtocol(p.id)"
        class="block p-2 rounded-xl text-xs hover:bg-purple-50/70 border border-gray-100 hover:border-purple-200 transition group cursor-pointer"
      >
        <div class="flex items-center justify-between">
          <span class="font-semibold text-gray-800 group-hover:text-[#833dff] truncate">{{ p.name }}</span>
          <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 rounded">✓</span>
        </div>
        <div class="flex items-center justify-between text-[10px] text-gray-400 mt-1 font-mono">
          <span>{{ p.execution_time || 'N/A' }}</span>
          <span>{{ p.num_figures || (p.figures ? p.figures.length : 0) }} plots</span>
        </div>
      </a>
    </div>
  </div>

  <div v-else class="flex flex-col items-center gap-1.5 w-full">
    <!-- Collapsed Quick Actions for Report Page -->
    <button
      @click="$emit('print-pdf')"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer"
      title="Print to PDF"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
      </svg>
    </button>

    <button
      @click="$emit('regenerate')"
      :disabled="regenerating"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition disabled:opacity-50 cursor-pointer"
      title="Regenerate Plots"
    >
      <svg
        class="w-4 h-4 text-[#833dff]"
        :class="regenerating ? 'animate-spin' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>

    <div class="w-6 border-b border-gray-200/80 my-1"></div>

    <!-- Routine Count Badge -->
    <div
      v-if="protocols?.length"
      class="text-[10px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded font-mono"
      :title="`Protocol Summary (${protocols.length} routines)`"
    >
      {{ protocols.length }}
    </div>

    <!-- Square Boxes with First Letters -->
    <a
      v-for="p in protocols"
      :key="p.id"
      @click.prevent="scrollToProtocol(p.id)"
      class="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs font-mono transition cursor-pointer relative shadow-2xs group/proto shrink-0 select-none"
      :class="p.status === 'error'
        ? 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-500 hover:text-white'
        : 'bg-purple-50 text-purple-800 border border-purple-100 hover:bg-[#833dff] hover:text-white hover:border-[#833dff]'"
      :title="`${p.name} (${p.execution_time || 'N/A'}, ${p.num_figures || (p.figures ? p.figures.length : 0)} plots)`"
    >
      <span>{{ getInitial(p.name) }}</span>
      <span
        class="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border border-white"
        :class="p.status === 'error' ? 'bg-amber-500' : 'bg-emerald-500'"
      ></span>
    </a>
  </div>
</template>

<script setup>
defineProps({
  protocols: { type: Array, default: () => [] },
  isCollapsed: { type: Boolean, default: false },
  regenerating: { type: Boolean, default: false }
})

defineEmits(['select-protocol', 'regenerate', 'print-pdf'])

function getInitial(name) {
  if (!name) return '?'
  const clean = name.replace(/^[^a-zA-Z0-9]+/, '')
  return (clean[0] || name[0] || '?').toUpperCase()
}

function scrollToProtocol(id) {
  const el = document.getElementById(`proto-${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>
