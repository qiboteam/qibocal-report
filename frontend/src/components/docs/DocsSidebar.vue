<template>
  <aside class="space-y-6">
    <div class="bm-card p-4 sm:p-5 border border-gray-200 bg-white rounded-2xl shadow-xs">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">
          Documentation
        </h2>
        <span class="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-[#833dff]">
          v0.1.0
        </span>
      </div>

      <!-- Doc Search / Filter Filter -->
      <div class="relative mb-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter topics..."
          class="w-full text-xs px-3 py-2 pl-8 rounded-xl border-0 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#833dff] transition"
        />
        <svg
          class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <!-- Navigation Sections & Subpages -->
      <nav class="space-y-4">
        <div v-for="section in filteredNav" :key="section.section" class="space-y-1">
          <button
            type="button"
            @click="$emit('select', section.path || section.items[0].path)"
            class="w-full text-left text-[11px] font-bold uppercase tracking-wider px-2 py-1 rounded-lg transition flex items-center justify-between cursor-pointer hover:bg-gray-100"
            :class="activeDoc === section.path ? 'text-[#833dff] bg-purple-50/70' : 'text-gray-500 hover:text-gray-900'"
            :title="`View ${section.section}`"
          >
            <span>{{ section.section }}</span>
          </button>
          <div class="space-y-0.5">
            <button
              v-for="item in section.items"
              :key="item.id"
              @click="$emit('select', item.path)"
              class="w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition flex items-center justify-between group cursor-pointer"
              :class="activeDoc === item.path
                ? 'bg-purple-50 text-[#833dff] font-semibold border-l-2 border-[#833dff]'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
            >
              <span class="truncate">{{ item.title }}</span>
              <svg
                class="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity"
                :class="activeDoc === item.path ? 'opacity-100 text-[#833dff]' : 'text-gray-400'"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </nav>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  nav: {
    type: Array,
    required: true
  },
  activeDoc: {
    type: String,
    required: true
  }
})

defineEmits(['select'])

const searchQuery = ref('')

const filteredNav = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return props.nav
  return props.nav
    .map(section => {
      const matchedItems = section.items.filter(
        i => i.title.toLowerCase().includes(q) ||
             (i.description && i.description.toLowerCase().includes(q))
      )
      return { ...section, items: matchedItems }
    })
    .filter(section => section.items.length > 0)
})
</script>
