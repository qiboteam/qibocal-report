<template>
  <div>
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
</template>

<script setup>
defineProps({
  protocols: { type: Array, default: () => [] }
})

function scrollToProtocol(id) {
  const el = document.getElementById(`proto-${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>
