<template>
  <div
    class="overflow-y-auto p-3 flex flex-col shrink-0 space-y-1"
    :style="!isCollapsed ? { height: `${height}px` } : {}"
  >
    <!-- Search Page -->
    <router-link
      to="/dashboard"
      class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
      :class="$route.path === '/dashboard' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <span v-if="!isCollapsed">Search & Browse</span>
    </router-link>

    <!-- Current Report -->
    <router-link
      v-if="currentReportId"
      :to="`/reports/${currentReportId}`"
      class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
      :class="$route.path.startsWith('/reports') ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <span v-if="!isCollapsed" class="truncate">Current Report</span>
    </router-link>

    <!-- Docs Button -->
    <router-link
      to="/docs"
      class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
      :class="$route.path === '/docs' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
    >
      <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
      <span v-if="!isCollapsed">Documentation</span>
    </router-link>
  </div>
</template>

<script setup>
defineProps({
  isCollapsed: { type: Boolean, default: false },
  currentReportId: { type: String, default: null },
  height: { type: Number, default: 145 }
})
</script>
