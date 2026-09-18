<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar -->
    <sidebar />

    <!-- Main Content Panel -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Top Bar: Header, Active Server info, Refresh -->
      <div
        class="sticky top-0 bg-[#f7f7f7]/90 backdrop-blur-md px-4 sm:px-6 py-4 border-b border-gray-200/70 z-20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 min-w-0"
      >
        <div class="min-w-0">
          <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
            Statistics & Insights
          </h1>
        </div>

        <div class="flex items-center gap-2.5 shrink-0">
          <!-- Active Server Indicator -->
          <div
            class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs bg-white border border-gray-200 shadow-2xs max-w-[200px]"
            :title="activeServer?.url || 'Local Instance'"
          >
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :class="connectionError ? 'bg-red-500' : loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'"
            ></span>
            <span class="text-gray-400 text-[11px] shrink-0">Server:</span>
            <span class="font-semibold text-gray-700 truncate">
              {{ activeServer?.name || "Local Instance" }}
            </span>
          </div>

          <!-- Refresh Button -->
          <button
            @click="loadStats"
            :disabled="loading"
            class="px-2.5 py-1.5 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50 shrink-0"
            title="Refresh statistics"
          >
            <svg
              class="w-3.5 h-3.5"
              :class="loading ? 'animate-spin text-[#833dff]' : ''"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="p-4 sm:p-6 w-full max-w-full box-border min-w-0 space-y-5 pb-12">
        <!-- Error Banner -->
        <div
          v-if="connectionError"
          class="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 min-w-0"
        >
          <div class="min-w-0">
            <div class="font-bold text-xs uppercase tracking-wider mb-0.5">Connection Error</div>
            <div class="text-xs truncate">{{ connectionError }}</div>
          </div>
          <button
            @click="loadStats"
            class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading && !stats" class="text-center py-20">
          <div class="inline-flex items-center gap-2 text-sm text-purple-700 font-medium">
            <svg class="animate-spin h-5 w-5 text-[#833dff]" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading aggregated statistics...
          </div>
        </div>

        <template v-else-if="stats">
          <!-- Top Row: High-Level Metric Tiles -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 min-w-0">
            <!-- Total Runs -->
            <div class="bm-card p-4 flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-purple-50 text-[#833dff] flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ totalReportsCount }}</div>
                <span class="text-[11px] text-gray-400 truncate block">Total Runs</span>
              </div>
            </div>

            <!-- Total Platforms -->
            <div class="bm-card p-4 flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ platformsList.length }}</div>
                <span class="text-[11px] text-gray-400 truncate block">Platforms</span>
              </div>
            </div>

            <!-- Unique Protocols -->
            <div class="bm-card p-4 flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ protocolsList.length }}</div>
                <span class="text-[11px] text-gray-400 truncate block">Routines</span>
              </div>
            </div>

            <!-- Calibration Scientists -->
            <div class="bm-card p-4 flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ authorsList.length }}</div>
                <span class="text-[11px] text-gray-400 truncate block">Authors</span>
              </div>
            </div>

            <!-- Applied Labels -->
            <div class="bm-card p-4 flex items-center gap-3 col-span-2 sm:col-span-1">
              <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              <div class="min-w-0">
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ tagsList.length }}</div>
                <span class="text-[11px] text-gray-400 truncate block">Applied labels</span>
              </div>
            </div>
          </div>

          <!-- Main Two-Column Layout: Left (Platforms, Authors, Tags, Activity) & Right (Reports per Protocol) -->
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-5 min-w-0 w-full items-start">
            <!-- Left Column: Compact Metrics -->
            <div class="space-y-5 min-w-0 flex flex-col">
              <!-- Platform Breakdown Card -->
              <stat-breakdown-card
                title="By Platform"
                count-label="platforms"
                :items="platformsList"
                :total="totalReportsCount"
                empty-text="No platform data found"
                dot-class="bg-[#833dff]"
                hover-class="hover:bg-purple-50/60 hover:border-purple-100"
                item-label-class="font-mono text-gray-800 group-hover:text-[#833dff]"
                bar-gradient-class="bg-gradient-to-r from-[#833dff] to-purple-400"
                arrow-class="text-[#833dff]"
                @select="name => filterBy('platform', name)"
              />

              <!-- Author Breakdown Card -->
              <stat-breakdown-card
                title="By Author"
                count-label="authors"
                :items="authorsList"
                :total="totalReportsCount"
                empty-text="No author data found"
                dot-class="bg-blue-500"
                hover-class="hover:bg-blue-50/60 hover:border-blue-100"
                item-label-class="text-gray-800 group-hover:text-blue-700"
                bar-gradient-class="bg-gradient-to-r from-blue-500 to-cyan-400"
                arrow-class="text-blue-600"
                @select="name => filterBy('author', name)"
              >
                <template #prefix="{ item }">
                  <div class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-[10px] flex items-center justify-center shrink-0 uppercase font-mono">
                    {{ (item.name && item.name[0]) || '?' }}
                  </div>
                </template>
              </stat-breakdown-card>

              <!-- Tags Breakdown Card -->
              <stat-breakdown-card
                title="By Tag / Label"
                count-label="tags"
                :items="tagsList"
                :total="totalReportsCount"
                empty-text="No tagged reports found"
                dot-class="bg-amber-500"
                hover-class="hover:bg-amber-50/60 hover:border-amber-100"
                item-label-class="text-gray-800 group-hover:text-amber-700"
                bar-gradient-class="bg-gradient-to-r from-amber-500 to-yellow-400"
                arrow-class="text-amber-600"
                @select="name => filterBy('label', name)"
              >
                <template #prefix="{ item }">
                  <span class="w-2 h-2 rounded-full bg-amber-400 shrink-0"></span>
                </template>
              </stat-breakdown-card>

              <!-- Activity Over Time Timeline Card -->
              <div class="bm-card p-4 sm:p-5 flex flex-col min-w-0">
                <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3 min-w-0">
                  <div class="flex items-center gap-2 min-w-0">
                    <div class="w-2.5 h-2.5 rounded-full bg-purple-600 shrink-0"></div>
                    <h2 class="text-xs sm:text-sm font-bold text-gray-900 uppercase tracking-wider truncate">
                      Activity Over Time
                    </h2>
                  </div>
                  <span class="text-xs text-gray-400 font-mono shrink-0">{{ dateBins.length }} dates</span>
                </div>

                <div v-if="dateBins.length === 0" class="py-6 text-center text-xs text-gray-400 italic">
                  No date history available
                </div>

                <div v-else class="flex flex-col justify-end min-w-0 w-full">
                  <div class="h-28 sm:h-32 w-full max-w-full min-w-0 bg-gray-50 p-2 rounded-lg border border-gray-100 overflow-hidden flex items-end gap-1 sm:gap-1.5 relative box-border">
                    <div
                      v-for="bin in dateBins"
                      :key="bin.date"
                      @click="filterBy('date', bin.date)"
                      class="flex-1 min-w-[2px] h-full relative group cursor-pointer"
                      :title="`${bin.date}: ${bin.count} report${bin.count === 1 ? '' : 's'}`"
                    >
                      <div
                        class="w-full bg-[#833dff] group-hover:bg-[#6c2bd9] rounded-t transition-all duration-200 absolute bottom-0"
                        :style="{ height: `${Math.max(8, getPercentage(bin.count, maxDateCount))}%` }"
                      ></div>
                    </div>
                  </div>

                  <div v-if="dateBins.length > 0" class="flex justify-between text-[10px] text-gray-400 mt-1.5 font-mono px-0.5 overflow-hidden">
                    <span class="truncate min-w-0">{{ dateBins[0]?.date }}</span>
                    <span v-if="dateBins.length > 1" class="truncate min-w-0 text-right">{{ dateBins[dateBins.length - 1]?.date }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column: By Protocol with Search -->
            <div class="min-w-0 flex flex-col">
              <div class="bm-card p-4 sm:p-5 flex flex-col min-w-0">
                <div class="pb-3 border-b border-gray-100 mb-3 space-y-2.5 min-w-0">
                  <div class="flex items-center justify-between min-w-0">
                    <div class="flex items-center gap-2 min-w-0">
                      <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0"></div>
                      <h2 class="text-xs sm:text-sm font-bold text-gray-900 uppercase tracking-wider truncate">
                        By Protocol
                      </h2>
                    </div>
                    <span class="text-xs text-gray-400 font-mono shrink-0">{{ protocolsList.length }} protocols</span>
                  </div>
                  <!-- Protocol Search Filter -->
                  <div class="relative w-full min-w-0">
                    <div class="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-gray-400">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <input
                      v-model="protocolSearch"
                      type="text"
                      placeholder="Filter protocols..."
                      class="w-full text-xs pl-8 pr-3 py-1.5 bg-gray-50 border-0 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#833dff]"
                    />
                  </div>
                </div>

                <div v-if="filteredProtocols.length === 0" class="py-8 text-center text-xs text-gray-400 italic">
                  {{ protocolSearch ? 'No matching protocols' : 'No protocol data found' }}
                </div>

                <div v-else class="space-y-2 min-w-0">
                  <div
                    v-for="proto in filteredProtocols"
                    :key="proto.name"
                    @click="filterBy('protocol', proto.name)"
                    class="group p-2.5 rounded-xl hover:bg-emerald-50/60 transition cursor-pointer border border-transparent hover:border-emerald-100 min-w-0"
                    :title="`Filter table by protocol: ${proto.name}`"
                  >
                    <div class="flex items-center justify-between mb-1 min-w-0 gap-2">
                      <span class="font-mono text-xs font-semibold text-gray-800 group-hover:text-emerald-700 transition truncate min-w-0 flex-1">
                        {{ proto.name }}
                      </span>
                      <div class="flex items-center gap-1.5 shrink-0">
                        <span class="text-xs font-bold font-mono text-gray-900">{{ proto.count }}</span>
                        <span class="text-xs text-emerald-600 opacity-0 group-hover:opacity-100 transition font-semibold">&rarr;</span>
                      </div>
                    </div>
                    <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        class="bg-gradient-to-r from-emerald-500 to-teal-400 h-1.5 rounded-full transition-all duration-300"
                        :style="{ width: `${getPercentage(proto.count, maxProtocolCount)}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { state, ensureServersLoaded } from '../store.js'
import Sidebar from '../components/Sidebar.vue'
import StatBreakdownCard from '../components/statistics/StatBreakdownCard.vue'
import { useStatisticsData } from '../composables/useStatisticsData.js'

const {
  stats,
  loading,
  connectionError,
  protocolSearch,
  activeServer,
  totalReportsCount,
  platformsList,
  protocolsList,
  filteredProtocols,
  maxProtocolCount,
  authorsList,
  tagsList,
  dateBins,
  maxDateCount,
  getPercentage,
  filterBy,
  loadStats
} = useStatisticsData()

onMounted(async () => {
  await ensureServersLoaded()
  loadStats()
})

watch(() => state.activeServer, () => {
  loadStats()
})
</script>
