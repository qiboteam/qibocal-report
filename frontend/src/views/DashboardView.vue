<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar (Issue #3) -->
    <sidebar
      :filter-stats="filterStats"
      :selected-author="filters.author"
      :selected-protocols="filters.protocols"
      :selected-labels="filters.labels"
      :selected-count="selectedReports.length"
      @update-filter="onUpdateFilter"
      @toggle-protocol="toggleProtocol"
      @toggle-label="toggleLabel"
      @reset-filters="resetFilters"
      @open-label="openLabelModal"
      @open-unlabel="openUnlabelModal"
      @open-author="openAuthorModal"
      @open-delete="openDeleteModal"
      @clear-selection="clearSelection"
    />


    <!-- Main Content Panel (Issue #3) -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Top Bar: Search, View Mode Switcher, Active Server info -->
      <div class="sticky top-0 bg-[#f7f7f7]/90 backdrop-blur-md px-6 py-4 border-b border-gray-200/70 z-20">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <!-- Full-text search input -->
          <div class="relative flex-1 max-w-md">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              v-model="filters.q"
              type="text"
              placeholder="Search reports by platform, tags, protocols, author..."
              class="w-full pl-9 pr-4 py-2 bg-white rounded-xl text-xs sm:text-sm border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff] shadow-xs"
            />
          </div>

          <!-- Controls: View Mode & Sort -->
          <div class="flex items-center gap-2">
            <!-- Sort dropdown -->
            <select
              v-model="filters.sort_by"
              class="text-xs py-2 px-3 bg-white border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] text-gray-700 shadow-xs"
            >
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="platform">Platform A-Z</option>
            </select>

            <!-- Visualization Mode Switcher: Table (default) vs Cards (Issue #3) -->
            <div class="flex items-center bg-white p-0.5 rounded-xl border border-gray-200 shadow-xs">
              <button
                @click="viewMode = 'table'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                :class="viewMode === 'table' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-500 hover:text-gray-800'"
                title="Table view (Default)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                @click="viewMode = 'cards'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                :class="viewMode === 'cards' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-500 hover:text-gray-800'"
                title="Horizontal cards view (Inspire style)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Active Filter Pills -->
        <div v-if="hasActiveFilters" class="flex flex-wrap items-center gap-1.5 mt-2.5">
          <span class="text-[11px] text-gray-500 font-medium">Active Filters:</span>
          <span
            v-if="filters.author"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800"
          >
            Author: {{ filters.author }}
            <button @click="filters.author = ''; fetchReports()" class="hover:text-black">&times;</button>
          </span>
          <span
            v-for="p in filters.protocols"
            :key="p"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            {{ p }}
            <button @click="toggleProtocol(p)" class="hover:text-black">&times;</button>
          </span>
          <span
            v-for="l in filters.labels"
            :key="l"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Tag: {{ l }}
            <button @click="toggleLabel(l)" class="hover:text-black">&times;</button>
          </span>
          <span
            v-if="filters.date"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Date: {{ filters.date }}
            <button @click="filters.date = ''; fetchReports()" class="hover:text-black">&times;</button>
          </span>
        </div>
      </div>

      <!-- Main Results Area -->
      <div class="p-6">
        <!-- Results Count & Active Server Indicator -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div class="flex items-center gap-3">
            <h2 class="text-sm font-bold text-gray-700 uppercase tracking-wider">
              Calibration Reports <span v-if="!loading">({{ totalReports }})</span><span v-else class="text-gray-400 font-normal text-xs font-mono">(loading...)</span>
            </h2>
            <!-- Active Server Indicator Badge -->
            <div
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs bg-white border border-gray-200 shadow-2xs"
              :title="activeServer?.url || 'Local Instance'"
            >
              <span
                class="w-2 h-2 rounded-full"
                :class="connectionError ? 'bg-red-500' : loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'"
              ></span>
              <span class="text-gray-400 text-[11px]">Server:</span>
              <span class="font-semibold text-gray-700 max-w-[120px] sm:max-w-[200px] truncate">
                {{ activeServer?.name || 'Local Instance' }}
              </span>
              <span class="text-[10px] font-mono text-gray-400 max-w-[150px] sm:max-w-[220px] truncate hidden sm:inline">
                ({{ activeServer?.url || 'local' }})
              </span>
            </div>
          </div>
          <span v-if="loading" class="text-xs text-purple-600 font-medium animate-pulse">Loading reports...</span>
          <span v-else-if="totalReports > 0" class="text-xs text-gray-400">Page {{ currentPage }} of {{ totalPages }}</span>
          <span v-else class="text-xs text-gray-400">0 matches</span>
        </div>

        <!-- Connection Error Banner -->
        <div
          v-if="connectionError"
          class="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div>
            <div class="font-bold text-xs">Connection Error</div>
            <div class="text-xs mt-0.5 text-red-600">{{ connectionError }}</div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="refreshData"
              class="px-3 py-1 bg-white border border-red-200 rounded-lg text-xs font-semibold hover:bg-red-50 transition"
            >
              Retry
            </button>
            <router-link
              to="/servers"
              class="px-3 py-1 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition"
            >
              Manage Servers
            </router-link>
          </div>
        </div>

        <!-- Bulk Success Message Banner -->
        <div
          v-if="bulkSuccessMessage"
          class="mb-4 bg-emerald-50 text-emerald-800 border border-emerald-200 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between gap-2 shadow-2xs animate-fade-in"
        >
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="font-medium">{{ bulkSuccessMessage }}</span>
          </div>
          <button @click="bulkSuccessMessage = ''" class="hover:text-emerald-950 font-bold cursor-pointer">&times;</button>
        </div>


        <!-- Loading State: immediately replaces reports when switching servers or querying -->
        <div
          v-if="loading"
          class="bg-white rounded-2xl p-12 text-center border border-gray-200 shadow-sm max-w-lg mx-auto my-8 flex flex-col items-center justify-center animate-fade-in"
        >
          <div class="w-8 h-8 border-3 border-[#833dff] border-t-transparent rounded-full animate-spin mb-3"></div>
          <h3 class="font-semibold text-sm text-gray-900">Loading calibration reports...</h3>
          <p class="text-xs text-gray-500 mt-1">
            Querying <span class="font-medium text-gray-700">{{ activeServer?.name || 'server' }}</span>
            <span v-if="activeServer?.url" class="font-mono text-[11px] text-gray-400"> ({{ activeServer.url }})</span>
          </p>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="displayedReports.length === 0 && !connectionError"
          class="bg-white rounded-2xl p-12 text-center border border-gray-200 shadow-sm max-w-lg mx-auto my-8"
        >
          <div class="w-12 h-12 rounded-xl bg-purple-50 text-[#833dff] flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="font-bold text-base text-gray-900">No calibration reports found</h3>
          <p class="text-xs text-gray-500 mt-1">Try adjusting your filters or point the server to a valid reports folder.</p>
          <button
            @click="resetFilters"
            class="mt-4 px-4 py-2 rounded-xl text-xs font-semibold bm-btn-secondary"
          >
            Reset All Filters
          </button>
        </div>

        <!-- Table View (Default, Issue #3) -->
        <report-table
          v-else-if="viewMode === 'table'"
          :reports="displayedReports"
          :selected="selectedReports"
          @select="openReport"
          @toggle-select="toggleSelect"
          @toggle-select-all="toggleSelectAll"
          @remove-tag="handleRemoveTag"
          @edit-author="handleEditAuthor"
        />

        <!-- Full-size Horizontal Cards View (Inspire style, Issue #3) -->
        <report-cards
          v-else
          :reports="displayedReports"
          :selected="selectedReports"
          @select="openReport"
          @toggle-select="toggleSelect"
          @remove-tag="handleRemoveTag"
          @edit-author="handleEditAuthor"
        />

        <!-- Pagination Controls -->
        <div
          v-if="!loading && totalReports > 0"
          class="mt-5 flex flex-col sm:flex-row items-center justify-between gap-4 bg-white px-4 py-3 rounded-2xl border border-gray-200 shadow-2xs text-xs select-none"
        >
          <!-- Left: Range display & Page size selector -->
          <div class="flex items-center gap-3 text-gray-500 flex-wrap">
            <span>
              Showing
              <strong class="font-semibold text-gray-800">{{ paginationRange.start }}</strong>
              to
              <strong class="font-semibold text-gray-800">{{ paginationRange.end }}</strong>
              of
              <strong class="font-semibold text-gray-800">{{ totalReports }}</strong>
              reports
            </span>
            <span class="text-gray-300">|</span>
            <div class="flex items-center gap-1.5">
              <span class="text-gray-400">Show:</span>
              <select
                v-model="pageSize"
                @change="onPageSizeChange"
                class="px-2 py-1 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#833dff] cursor-pointer"
              >
                <option :value="10">10 / page</option>
                <option :value="25">25 / page</option>
                <option :value="50">50 / page</option>
              </select>
            </div>
          </div>

          <!-- Right: Page Navigation Buttons -->
          <div class="flex items-center gap-1">
            <!-- Previous Button -->
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage <= 1"
              class="px-2.5 py-1.5 rounded-lg border border-gray-200 font-medium transition flex items-center gap-1"
              :class="currentPage > 1
                ? 'bg-white text-gray-700 hover:bg-purple-50 hover:text-[#833dff] hover:border-purple-200 cursor-pointer'
                : 'bg-gray-50 text-gray-300 border-gray-100 cursor-not-allowed'"
              title="Previous page"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              <span>Prev</span>
            </button>

            <!-- Numeric Page Buttons with Ellipses -->
            <template v-for="(p, idx) in visiblePages" :key="idx">
              <span v-if="p === '...'" class="px-2 py-1 text-gray-400">...</span>
              <button
                v-else
                @click="goToPage(p)"
                class="min-w-[30px] h-[30px] rounded-lg text-xs font-semibold transition cursor-pointer flex items-center justify-center"
                :class="p === currentPage
                  ? 'bg-[#833dff] text-white shadow-2xs'
                  : 'bg-white border border-gray-200 text-gray-700 hover:bg-purple-50 hover:text-[#833dff] hover:border-purple-200'"
              >
                {{ p }}
              </button>
            </template>

            <!-- Next Button -->
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage >= totalPages"
              class="px-2.5 py-1.5 rounded-lg border border-gray-200 font-medium transition flex items-center gap-1"
              :class="currentPage < totalPages
                ? 'bg-white text-gray-700 hover:bg-purple-50 hover:text-[#833dff] hover:border-purple-200 cursor-pointer'
                : 'bg-gray-50 text-gray-300 border-gray-100 cursor-not-allowed'"
              title="Next page"
            >
              <span>Next</span>
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Label Modal -->
    <div
      v-if="showLabelModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
      @click.self="showLabelModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
            <svg class="w-5 h-5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            Add Label to Reports
          </div>
          <button @click="showLabelModal = false" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-3">
            Applying this label will add it to the metadata of the
            <strong class="text-gray-800">{{ selectedReports.length }}</strong> selected report(s).
          </p>

          <label class="block text-xs font-semibold text-gray-700 mb-1">Label / Tag Name</label>
          <input
            v-model="newLabelText"
            type="text"
            placeholder="e.g. validated, benchmark, fast..."
            class="w-full text-xs px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:bg-white transition"
            @keyup.enter="applyBulkLabel"
          />

          <!-- Existing suggestions -->
          <div v-if="filterStats?.tags?.length" class="mt-3">
            <span class="text-[11px] text-gray-400 font-medium">Existing tags:</span>
            <div class="flex flex-wrap gap-1 mt-1.5 max-h-20 overflow-y-auto">
              <button
                v-for="t in filterStats.tags"
                :key="t"
                type="button"
                @click="newLabelText = t"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 font-mono transition cursor-pointer"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <div v-if="bulkError" class="mt-3 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
            {{ bulkError }}
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button
            @click="showLabelModal = false"
            class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyBulkLabel"
            :disabled="!newLabelText.trim() || bulkActionInProgress"
            class="bm-btn-primary px-4 py-1.5 text-xs shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <span v-if="bulkActionInProgress" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Apply Label
          </button>
        </div>
      </div>
    </div>

    <!-- Unlabel Modal -->
    <div
      v-if="showUnlabelModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
      @click.self="showUnlabelModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
            <svg class="w-5 h-5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Remove Label from Reports
          </div>
          <button @click="showUnlabelModal = false" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-3">
            Select or enter a label to remove from the
            <strong class="text-gray-800">{{ selectedReports.length }}</strong> selected report(s).
          </p>

          <label class="block text-xs font-semibold text-gray-700 mb-1">Label / Tag to Remove</label>
          <input
            v-model="newUnlabelText"
            type="text"
            placeholder="Select a tag below or type name..."
            class="w-full text-xs px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:bg-white transition"
            @keyup.enter="applyBulkUnlabel"
          />

          <!-- Available tags on selected reports -->
          <div v-if="tagsOnSelectedReports.length" class="mt-3">
            <span class="text-[11px] text-gray-400 font-medium">Tags on selected reports:</span>
            <div class="flex flex-wrap gap-1 mt-1.5 max-h-24 overflow-y-auto">
              <button
                v-for="t in tagsOnSelectedReports"
                :key="t"
                type="button"
                @click="newUnlabelText = t"
                class="px-2 py-0.5 rounded text-[11px] font-medium font-mono transition cursor-pointer"
                :class="newUnlabelText === t ? 'bg-[#833dff] text-white' : 'bg-purple-50 hover:bg-purple-100 text-purple-700'"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <div v-if="bulkError" class="mt-3 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
            {{ bulkError }}
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button
            @click="showUnlabelModal = false"
            class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyBulkUnlabel"
            :disabled="!newUnlabelText.trim() || bulkActionInProgress"
            class="bm-btn-primary px-4 py-1.5 text-xs shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <span v-if="bulkActionInProgress" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Remove Label
          </button>
        </div>
      </div>
    </div>

    <!-- Author Modal -->
    <div
      v-if="showAuthorModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
      @click.self="showAuthorModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
            <svg class="w-5 h-5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {{ targetReportIdForAuthor ? 'Edit Report Author' : 'Set Author for Reports' }}
          </div>
          <button @click="showAuthorModal = false" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-500 mb-3">
            <template v-if="targetReportIdForAuthor">
              Modify the author name for this calibration report.
            </template>
            <template v-else>
              Set the author for the
              <strong class="text-gray-800">{{ selectedReports.length }}</strong> selected report(s).
            </template>
          </p>

          <label class="block text-xs font-semibold text-gray-700 mb-1">Author Name</label>
          <input
            v-model="newAuthorText"
            type="text"
            placeholder="e.g. Alice, Bob, lab_team..."
            class="w-full text-xs px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:bg-white transition"
            @keyup.enter="applyAuthor"
          />

          <!-- Author suggestions -->
          <div v-if="authorSuggestions.length" class="mt-3">
            <span class="text-[11px] text-gray-400 font-medium">Suggested authors:</span>
            <div class="flex flex-wrap gap-1 mt-1.5 max-h-24 overflow-y-auto">
              <button
                v-for="a in authorSuggestions"
                :key="a"
                type="button"
                @click="newAuthorText = a"
                class="px-2 py-0.5 rounded text-[11px] font-medium transition cursor-pointer"
                :class="newAuthorText === a ? 'bg-[#833dff] text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'"
              >
                {{ a }}
              </button>
            </div>
          </div>

          <div v-if="bulkError" class="mt-3 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
            {{ bulkError }}
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button
            @click="showAuthorModal = false"
            class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyAuthor"
            :disabled="bulkActionInProgress"
            class="bm-btn-primary px-4 py-1.5 text-xs shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <span v-if="bulkActionInProgress" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Save Author
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
      @click.self="showDeleteModal = false"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2 text-red-600 font-bold text-base">
            <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Confirm Deletion
          </div>
          <button @click="showDeleteModal = false" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
        </div>

        <div class="mt-4">
          <p class="text-xs text-gray-700 leading-relaxed">
            Are you sure you want to permanently delete
            <strong class="text-red-600">{{ selectedReports.length }}</strong> report folder{{ selectedReports.length > 1 ? 's' : '' }} from the server?
          </p>
          <p class="text-[11px] text-gray-400 mt-1">
            This will remove the report directory and all underlying data files. This action cannot be undone.
          </p>

          <div v-if="bulkError" class="mt-3 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
            {{ bulkError }}
          </div>
        </div>

        <div class="mt-6 flex items-center justify-end gap-2">
          <button
            @click="showDeleteModal = false"
            class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyBulkDelete"
            :disabled="bulkActionInProgress"
            class="px-4 py-1.5 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <span v-if="bulkActionInProgress" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Delete {{ selectedReports.length }} Report{{ selectedReports.length > 1 ? 's' : '' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { state, addToHistory, apiFetch, ensureServersLoaded } from '../store.js'
import Sidebar from '../components/Sidebar.vue'
import ReportTable from '../components/ReportTable.vue'
import ReportCards from '../components/ReportCards.vue'

const router = useRouter()
const viewMode = ref('table') // default table
const reports = ref([])
const filterStats = ref(null)
const loading = ref(true)
const connectionError = ref(null)

// Pagination & Pre-fetch Cache State
const currentPage = ref(1)
const pageSize = ref(10)
const totalReports = ref(0)
const totalPages = ref(1)
const pageCache = new Map()

// Bulk Selection & Actions State
const selectedReports = ref([])
const showLabelModal = ref(false)
const showUnlabelModal = ref(false)
const showAuthorModal = ref(false)
const showDeleteModal = ref(false)

const newLabelText = ref('')
const newUnlabelText = ref('')
const newAuthorText = ref('')
const targetReportIdForAuthor = ref(null)

const bulkActionInProgress = ref(false)
const bulkError = ref(null)
const bulkSuccessMessage = ref('')

const activeServer = computed(() => state.activeServer)

const filters = reactive({
  q: '',
  author: '',
  date: '',
  protocols: [],
  labels: [],
  sort_by: 'date_desc'
})

const hasActiveFilters = computed(() => {
  return filters.author || filters.date || filters.protocols.length > 0 || filters.labels.length > 0
})

// Displayed reports for current page
const displayedReports = computed(() => reports.value || [])

function getFilterQueryKey() {
  const serverKey = state.activeServer?.id || state.activeServer?.url || 'local'
  const protos = [...filters.protocols].sort().join(',')
  const labels = [...filters.labels].sort().join(',')
  return `${serverKey}|${filters.q.trim().toLowerCase()}|${filters.author}|${filters.date}|${protos}|${labels}|${filters.sort_by}|${pageSize.value}`
}

function getCacheKey(p) {
  return `${getFilterQueryKey()}|p_${p}`
}

const paginationRange = computed(() => {
  if (totalReports.value === 0) return { start: 0, end: 0 }
  const start = (currentPage.value - 1) * pageSize.value + 1
  const end = Math.min(start + (reports.value?.length || 0) - 1, totalReports.value)
  return { start, end }
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages = []
  if (current <= 4) {
    for (let i = 1; i <= 5; i++) pages.push(i)
    pages.push('...')
    pages.push(total)
  } else if (current >= total - 3) {
    pages.push(1)
    pages.push('...')
    for (let i = total - 4; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    pages.push('...')
    pages.push(current - 1)
    pages.push(current)
    pages.push(current + 1)
    pages.push('...')
    pages.push(total)
  }
  return pages
})

function getAccessiblePages(current, total) {
  if (total <= 1) return []
  const accessible = new Set()
  if (current > 1) accessible.add(current - 1)
  if (current < total) accessible.add(current + 1)
  accessible.add(1)
  accessible.add(total)
  for (let p = Math.max(1, current - 2); p <= Math.min(total, current + 2); p++) {
    if (p >= 1 && p <= total) accessible.add(p)
  }
  accessible.delete(current)
  return Array.from(accessible).filter(p => p >= 1 && p <= total)
}

function prefetchAccessiblePages() {
  const current = currentPage.value
  const total = totalPages.value
  const targetPages = getAccessiblePages(current, total)

  for (const p of targetPages) {
    const key = getCacheKey(p)
    if (!pageCache.has(key)) {
      fetchReports(p, true /* isPrefetch */)
    }
  }
}

function goToPage(p) {
  if (p < 1 || p > totalPages.value || p === currentPage.value) return
  fetchReports(p, false)
}

function onPageSizeChange() {
  currentPage.value = 1
  pageCache.clear()
  fetchReports(1, false)
}

const tagsOnSelectedReports = computed(() => {
  const tags = new Set()
  const sel = selectedReports.value
  for (const r of reports.value) {
    if (sel.includes(r.id)) {
      for (const t of (r.tags || r.labels || [])) {
        if (t) tags.add(t)
      }
    }
  }
  return Array.from(tags)
})

const authorSuggestions = computed(() => {
  const authors = new Set()
  if (activeServer.value?.author_identities) {
    for (const canonical of Object.keys(activeServer.value.author_identities)) {
      authors.add(canonical)
    }
  }
  if (filterStats.value?.authors && Array.isArray(filterStats.value.authors)) {
    for (const a of filterStats.value.authors) {
      if (a && a !== 'Unknown') authors.add(a)
    }
  }
  return Array.from(authors)
})

onMounted(async () => {
  loading.value = true
  await ensureServersLoaded()
  await refreshData()
})

watch(
  () => [state.activeServer?.id, state.activeServer?.url],
  async ([newId, newUrl], [oldId, oldUrl]) => {
    if (newId !== oldId || newUrl !== oldUrl) {
      reports.value = []
      totalReports.value = 0
      currentPage.value = 1
      selectedReports.value = []
      filterStats.value = null
      pageCache.clear()
      loading.value = true
      connectionError.value = null
      await refreshData()
    }
  }
)

let searchDebounceTimeout = null
watch(
  () => filters.q,
  () => {
    if (searchDebounceTimeout) clearTimeout(searchDebounceTimeout)
    searchDebounceTimeout = setTimeout(() => {
      currentPage.value = 1
      pageCache.clear()
      fetchReports(1, false)
    }, 200)
  }
)

watch(
  () => filters.sort_by,
  () => {
    currentPage.value = 1
    pageCache.clear()
    fetchReports(1, false)
  }
)

async function refreshData() {
  loading.value = true
  connectionError.value = null
  reports.value = []
  totalReports.value = 0
  currentPage.value = 1
  filterStats.value = null
  pageCache.clear()
  await Promise.all([fetchStats(), fetchReports(1, false)])
}

async function fetchStats() {
  try {
    const res = await apiFetch('/api/reports/stats')
    if (res.ok) {
      filterStats.value = await res.json()
    } else {
      filterStats.value = null
    }
  } catch (err) {
    console.error('Failed to fetch stats', err)
    filterStats.value = null
  }
}

async function fetchReports(page = currentPage.value, isPrefetch = false) {
  const cacheKey = getCacheKey(page)

  if (pageCache.has(cacheKey)) {
    if (!isPrefetch) {
      const cached = pageCache.get(cacheKey)
      reports.value = cached.items
      totalReports.value = cached.total
      totalPages.value = cached.total_pages
      currentPage.value = cached.page
      loading.value = false
      connectionError.value = null
      prefetchAccessiblePages()
    }
    return
  }

  if (!isPrefetch) {
    loading.value = true
    connectionError.value = null
  }

  try {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(pageSize.value))
    if (filters.q.trim()) params.set('q', filters.q.trim())
    if (filters.sort_by) params.set('sort_by', filters.sort_by)
    if (filters.author) params.set('author', filters.author)
    if (filters.date) {
      params.set('start_date', filters.date)
      params.set('end_date', filters.date)
    }
    filters.protocols.forEach(p => params.append('protocol', p))
    filters.labels.forEach(l => params.append('label', l))

    const res = await apiFetch(`/api/reports?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      const items = Array.isArray(data) ? data : (data.items || [])
      const total = Array.isArray(data) ? data.length : (data.total ?? items.length)
      const total_pages = Array.isArray(data) ? 1 : (data.total_pages ?? 1)
      const page_num = Array.isArray(data) ? 1 : (data.page ?? page)

      const payload = {
        items,
        total,
        total_pages,
        page: page_num,
        page_size: pageSize.value
      }

      pageCache.set(cacheKey, payload)

      if (!isPrefetch) {
        reports.value = items
        totalReports.value = total
        totalPages.value = total_pages
        currentPage.value = page_num
        loading.value = false
        // Pre-fetch pages accessible from the page navigation
        prefetchAccessiblePages()
      }
    } else if (!isPrefetch) {
      connectionError.value = `Server responded with status ${res.status}`
      reports.value = []
      loading.value = false
    }
  } catch (err) {
    if (!isPrefetch) {
      console.error('Failed to fetch reports', err)
      connectionError.value = `Could not connect to ${activeServer.value?.name || 'server'} (${activeServer.value?.url || ''}): ${err.message || 'Network error'}`
      reports.value = []
      loading.value = false
    }
  }
}

function onUpdateFilter({ key, value }) {
  if (key === 'author') filters.author = value
  if (key === 'date') filters.date = value
  currentPage.value = 1
  pageCache.clear()
  fetchReports(1, false)
}

function toggleProtocol(name) {
  const idx = filters.protocols.indexOf(name)
  if (idx >= 0) filters.protocols.splice(idx, 1)
  else filters.protocols.push(name)
  currentPage.value = 1
  pageCache.clear()
  fetchReports(1, false)
}

function toggleLabel(name) {
  const idx = filters.labels.indexOf(name)
  if (idx >= 0) filters.labels.splice(idx, 1)
  else filters.labels.push(name)
  currentPage.value = 1
  pageCache.clear()
  fetchReports(1, false)
}

function resetFilters() {
  filters.q = ''
  filters.author = ''
  filters.date = ''
  filters.protocols = []
  filters.labels = []
  selectedReports.value = []
  currentPage.value = 1
  pageCache.clear()
  fetchReports(1, false)
}

function openReport(report) {
  state.currentReportId = report.id
  addToHistory(report)
  router.push(`/reports/${report.id}`)
}

// Bulk Selection Methods
function toggleSelect(id) {
  const idx = selectedReports.value.indexOf(id)
  if (idx >= 0) {
    selectedReports.value.splice(idx, 1)
  } else {
    selectedReports.value.push(id)
  }
}

function toggleSelectAll() {
  const currentIds = displayedReports.value.map(r => r.id)
  const allSelected = currentIds.length > 0 && currentIds.every(id => selectedReports.value.includes(id))
  if (allSelected) {
    selectedReports.value = selectedReports.value.filter(id => !currentIds.includes(id))
  } else {
    selectedReports.value = Array.from(new Set([...selectedReports.value, ...currentIds]))
  }
}

function clearSelection() {
  selectedReports.value = []
}

// Bulk & Item Actions
function openLabelModal() {
  newLabelText.value = ''
  bulkError.value = null
  showLabelModal.value = true
}

function openUnlabelModal() {
  newUnlabelText.value = ''
  bulkError.value = null
  showUnlabelModal.value = true
}

function openAuthorModal() {
  targetReportIdForAuthor.value = null
  newAuthorText.value = ''
  bulkError.value = null
  showAuthorModal.value = true
}

function openDeleteModal() {
  bulkError.value = null
  showDeleteModal.value = true
}

async function handleRemoveTag({ report, tag }) {
  if (!report?.id || !tag) return
  try {
    const encodedId = encodeURIComponent(report.id)
    const encodedTag = encodeURIComponent(tag)
    const res = await apiFetch(`/api/reports/${encodedId}/label/${encodedTag}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      if (Array.isArray(report.tags)) {
        report.tags = report.tags.filter(t => t !== tag)
      }
      if (Array.isArray(report.labels)) {
        report.labels = report.labels.filter(t => t !== tag)
      }
      bulkSuccessMessage.value = `Removed tag '${tag}' from report`
      setTimeout(() => { bulkSuccessMessage.value = '' }, 3000)
      fetchStats()
    }
  } catch (err) {
    console.error('Failed to remove tag', err)
  }
}

function handleEditAuthor(report) {
  targetReportIdForAuthor.value = report.id
  newAuthorText.value = report.author === 'Unknown' ? '' : report.author
  bulkError.value = null
  showAuthorModal.value = true
}

async function applyBulkLabel() {
  if (!newLabelText.value.trim() || selectedReports.value.length === 0) return
  bulkActionInProgress.value = true
  bulkError.value = null
  try {
    const res = await apiFetch('/api/reports/bulk-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'label',
        report_ids: selectedReports.value,
        label: newLabelText.value.trim()
      })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to apply label')
    }
    const data = await res.json()
    showLabelModal.value = false
    newLabelText.value = ''
    selectedReports.value = []
    bulkSuccessMessage.value = data.message || 'Label applied successfully'
    pageCache.clear()
    await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  } catch (err) {
    bulkError.value = err.message
  } finally {
    bulkActionInProgress.value = false
  }
}

async function applyBulkUnlabel() {
  if (!newUnlabelText.value.trim() || selectedReports.value.length === 0) return
  bulkActionInProgress.value = true
  bulkError.value = null
  try {
    const res = await apiFetch('/api/reports/bulk-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'unlabel',
        report_ids: selectedReports.value,
        label: newUnlabelText.value.trim()
      })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to remove label')
    }
    const data = await res.json()
    showUnlabelModal.value = false
    newUnlabelText.value = ''
    selectedReports.value = []
    bulkSuccessMessage.value = data.message || 'Label removed successfully'
    setTimeout(() => { bulkSuccessMessage.value = '' }, 4000)
    pageCache.clear()
    await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  } catch (err) {
    bulkError.value = err.message
  } finally {
    bulkActionInProgress.value = false
  }
}

async function applyAuthor() {
  const authorVal = newAuthorText.value.trim()
  const reportIds = targetReportIdForAuthor.value ? [targetReportIdForAuthor.value] : selectedReports.value
  if (reportIds.length === 0) return
  bulkActionInProgress.value = true
  bulkError.value = null
  try {
    const res = await apiFetch('/api/reports/bulk-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'author',
        report_ids: reportIds,
        author: authorVal
      })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to update author')
    }
    const data = await res.json()
    showAuthorModal.value = false
    targetReportIdForAuthor.value = null
    newAuthorText.value = ''
    selectedReports.value = []
    bulkSuccessMessage.value = data.message || 'Author updated successfully'
    setTimeout(() => { bulkSuccessMessage.value = '' }, 4000)
    pageCache.clear()
    await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  } catch (err) {
    bulkError.value = err.message
  } finally {
    bulkActionInProgress.value = false
  }
}

async function applyBulkDelete() {
  if (selectedReports.value.length === 0) return
  bulkActionInProgress.value = true
  bulkError.value = null
  try {
    const res = await apiFetch('/api/reports/bulk-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'delete',
        report_ids: selectedReports.value
      })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to delete reports')
    }
    const data = await res.json()
    showDeleteModal.value = false
    selectedReports.value = []
    bulkSuccessMessage.value = data.message || 'Reports deleted successfully'
    setTimeout(() => { bulkSuccessMessage.value = '' }, 4000)
    pageCache.clear()
    await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  } catch (err) {
    bulkError.value = err.message
  } finally {
    bulkActionInProgress.value = false
  }
}
</script>
