<template>
  <div
    class="overflow-y-auto shrink-0 flex flex-col space-y-1"
    :class="isCollapsed ? 'p-2 items-center' : 'p-3'"
    :style="!isCollapsed ? { height: `${height}px` } : {}"
  >
    <!-- Search Page -->
    <router-link
      to="/dashboard"
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path === '/dashboard' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Search & Browse"
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
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path.startsWith('/reports') ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Current Report"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <span v-if="!isCollapsed" class="truncate">Current Report</span>
    </router-link>

    <!-- Statistics -->
    <router-link
      to="/statistics"
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path === '/statistics' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Statistics"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <span v-if="!isCollapsed">Statistics</span>
    </router-link>

    <!-- Archives (Storage Explorer) -->
    <router-link
      to="/archives"
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path === '/archives' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Archives (Storage Explorer)"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
      </svg>
      <span v-if="!isCollapsed">Archives</span>
    </router-link>

    <!-- Docs Button -->
    <router-link
      to="/docs"
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path.startsWith('/docs') ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Documentation"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
      <span v-if="!isCollapsed">Documentation</span>
    </router-link>

    <button
      v-if="state.auth.enabled && state.auth.token"
      @click="handleLogout"
      class="border-0 bg-transparent rounded-xl text-xs font-semibold transition flex items-center text-gray-700 hover:bg-gray-100 cursor-pointer"
      :class="isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'"
      title="Log out"
    >
      <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H5a2 2 0 00-2 2v10a2 2 0 002 2h4m7-12l5 5-5 5m5-5H9" />
      </svg>
      <span v-if="!isCollapsed">Log out</span>
    </button>

    <!-- Server Admin Button (Admin only) -->
    <router-link
      v-if="isAdmin"
      to="/admin"
      class="rounded-xl text-xs font-semibold transition flex items-center"
      :class="[
        $route.path === '/admin' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100',
        isCollapsed ? 'w-9 h-9 justify-center' : 'gap-3 px-3 py-2'
      ]"
      title="Server Administration"
    >
      <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      <span v-if="!isCollapsed">Server Admin</span>
    </router-link>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { state, isAdmin, logoutActiveServer } from '../../store.js'

const router = useRouter()

function handleLogout() {
  logoutActiveServer()
  router.push('/servers')
}

defineProps({
  isCollapsed: { type: Boolean, default: false },
  currentReportId: { type: String, default: null },
  height: { type: Number, default: 215 }
})
</script>
