<template>
  <div class="min-h-screen bg-[#f7f7f7] py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <!-- Top Utility Nav: Back to Dashboard -->
      <div class="flex items-center justify-between pb-6 mb-6 border-b border-gray-200/60">
        <router-link
          to="/dashboard"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition cursor-pointer"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </router-link>

        <button
          @click="loadArchives"
          :disabled="loading"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition cursor-pointer disabled:opacity-50"
        >
          <svg
            class="w-3.5 h-3.5"
            :class="{ 'animate-spin': loading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 mb-3 shadow-2xs">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
          Archives & Storage Explorer
        </h1>
        <p class="mt-1.5 text-xs sm:text-sm text-gray-500 max-w-lg mx-auto">
          Explore, inspect, download, and restore consolidated report packages stored outside active views.
        </p>
      </div>

      <!-- Toast Message -->
      <div
        v-if="toastMessage"
        class="mb-6 p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl flex items-center justify-between border border-emerald-200 animate-fade-in shadow-2xs"
      >
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-emerald-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span>{{ toastMessage }}</span>
        </div>
        <button @click="toastMessage = ''" class="text-emerald-500 hover:text-emerald-700 text-sm font-bold">&times;</button>
      </div>

      <!-- Error Message -->
      <div
        v-if="errorMessage"
        class="mb-6 p-3 bg-red-50 text-red-700 text-xs rounded-xl flex items-center justify-between border border-red-200 animate-fade-in shadow-2xs"
      >
        <span>{{ errorMessage }}</span>
        <button @click="errorMessage = ''" class="text-red-500 hover:text-red-700 text-sm font-bold">&times;</button>
      </div>

      <!-- Summary Metrics Bar -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div class="bg-white p-4 rounded-2xl shadow-2xs border border-gray-100 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <div class="text-lg font-bold text-gray-900 leading-tight">{{ archives.length }}</div>
            <div class="text-[11px] text-gray-500">Total Archives</div>
          </div>
        </div>

        <div class="bg-white p-4 rounded-2xl shadow-2xs border border-gray-100 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-purple-50 text-[#833dff] flex items-center justify-center shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <div class="text-lg font-bold text-gray-900 leading-tight">{{ totalPreservedReports }}</div>
            <div class="text-[11px] text-gray-500">Archived Reports</div>
          </div>
        </div>

        <div class="bg-white p-4 rounded-2xl shadow-2xs border border-gray-100 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div>
            <div class="text-lg font-bold text-gray-900 leading-tight">{{ formatBytes(totalStoredSize) }}</div>
            <div class="text-[11px] text-gray-500">Archive Storage Used</div>
          </div>
        </div>
      </div>

      <!-- Filter / Search Box -->
      <div class="bg-white rounded-2xl shadow-2xs border border-gray-100 p-2 pl-4 flex items-center gap-2 mb-6">
        <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter archives by name, description, tags, protocols, platform..."
          class="border-0 outline-none w-full bg-transparent text-xs text-gray-900 placeholder-gray-400 focus:outline-none py-1.5"
        />
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="text-gray-400 hover:text-gray-600 p-1 text-xs"
        >
          Clear
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="py-16 text-center text-xs text-gray-500 flex flex-col items-center justify-center gap-2">
        <div class="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        Scanning archive storage...
      </div>

      <!-- Empty State -->
      <div
        v-else-if="archives.length === 0"
        class="bg-white rounded-2xl border border-gray-200/80 p-12 text-center max-w-md mx-auto shadow-2xs"
      >
        <div class="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
        </div>
        <h3 class="text-sm font-bold text-gray-900 mb-1">No Archives Created Yet</h3>
        <p class="text-xs text-gray-500 mb-4 leading-relaxed">
          Select one or multiple reports from the Dashboard, click <strong class="text-indigo-600">Archive</strong> in the floating action bar, and consolidate them here.
        </p>
        <router-link
          to="/dashboard"
          class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-2xs"
        >
          Go to Dashboard
        </router-link>
      </div>

      <!-- Filtered Empty State -->
      <div
        v-else-if="filteredArchives.length === 0"
        class="bg-white rounded-2xl border border-gray-200/80 p-12 text-center shadow-2xs"
      >
        <p class="text-xs text-gray-500">No archives match "{{ searchQuery }}".</p>
        <button
          @click="searchQuery = ''"
          class="mt-3 px-3 py-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition cursor-pointer"
        >
          Reset search
        </button>
      </div>

      <!-- Archives List -->
      <div v-else class="space-y-4">
        <div
          v-for="arc in filteredArchives"
          :key="arc.id"
          class="bg-white rounded-2xl border border-gray-100 hover:border-indigo-100 shadow-2xs hover:shadow-md transition p-5 flex flex-col gap-3"
        >
          <!-- Top Row: Archive Name, Edit, Created Date -->
          <div class="flex items-start justify-between gap-4">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-base font-bold text-gray-900 leading-snug">
                  {{ arc.name }}
                </h3>
                <button
                  @click="openEditModal(arc)"
                  class="text-gray-400 hover:text-indigo-600 p-1 rounded-lg hover:bg-gray-100 transition cursor-pointer"
                  title="Edit name or description"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
              </div>
              <div class="text-[11px] text-gray-400 font-mono mt-0.5">
                ID: {{ arc.id }} &bull; Created {{ formatDate(arc.created_at) }}
              </div>
            </div>

            <!-- Badges -->
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-semibold text-xs">
                {{ arc.report_count }} {{ arc.report_count === 1 ? 'report' : 'reports' }}
              </span>
              <span class="px-2.5 py-1 rounded-lg bg-gray-100 text-gray-700 font-mono text-xs">
                {{ formatBytes(arc.size_bytes) }}
              </span>
            </div>
          </div>

          <!-- Description -->
          <p v-if="arc.description" class="text-xs text-gray-600 leading-relaxed bg-gray-50/70 p-2.5 rounded-xl border border-gray-100">
            {{ arc.description }}
          </p>

          <!-- Captured Filters Chips -->
          <div v-if="hasArchiveFilters(arc)" class="flex flex-wrap items-center gap-1.5 text-[11px]">
            <span class="text-gray-400 font-medium">Recorded filters:</span>
            <span v-if="arc.filters?.search" class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
              search: {{ arc.filters.search }}
            </span>
            <span v-if="arc.filters?.subfolder" class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
              folder: {{ arc.filters.subfolder }}
            </span>
            <span v-for="tag in arc.filters?.tags || []" :key="'tag-' + tag" class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-mono">
              tag:{{ tag }}
            </span>
            <span v-for="proto in arc.filters?.protocols || []" :key="'proto-' + proto" class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-mono">
              protocol:{{ proto }}
            </span>
            <span v-for="plat in arc.filters?.platforms || []" :key="'plat-' + plat" class="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700">
              platform:{{ plat }}
            </span>
            <span v-for="auth in arc.filters?.authors || []" :key="'auth-' + auth" class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700">
              author:{{ auth }}
            </span>
          </div>

          <!-- Action Buttons Bar -->
          <div class="pt-2 border-t border-gray-100 flex items-center justify-between gap-2 flex-wrap">
            <div class="text-[11px] text-gray-400 truncate max-w-xs" :title="arc.zip_filename">
              {{ arc.zip_filename }}
            </div>

            <div class="flex items-center gap-2">
              <!-- Peak Content (Zero decompression) -->
              <button
                @click="openPeakModal(arc)"
                class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 transition flex items-center gap-1.5 cursor-pointer shadow-2xs"
                title="Inspect indexed reports without unzipping"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                Peak Content
              </button>

              <!-- Download ZIP -->
              <button
                @click="downloadArchive(arc)"
                class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-200/80 transition flex items-center gap-1.5 cursor-pointer shadow-2xs"
                title="Download full zip file"
              >
                <svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download ZIP
              </button>

              <!-- Restore to Active Reports -->
              <button
                @click="openRestoreModal(arc)"
                class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 transition flex items-center gap-1.5 cursor-pointer shadow-2xs"
                title="Extract reports back into active directory"
              >
                <svg class="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Restore
              </button>

              <!-- Delete Archive -->
              <button
                @click="openDeleteModal(arc)"
                class="p-1.5 text-xs font-semibold rounded-xl hover:bg-red-50 text-red-500 hover:text-red-700 transition cursor-pointer"
                title="Delete archive permanently"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Peak Modal -->
      <archive-peak-modal
        :show="showPeakModal"
        :archive="selectedArchiveForPeak"
        @close="showPeakModal = false"
        @restore-selected="handleRestoreSelectedFromPeak"
        @restore-all="handleRestoreAllFromPeak"
      />

      <!-- Edit Archive Modal -->
      <div
        v-if="showEditModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
        @click.self="showEditModal = false"
      >
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
          <div class="flex items-center justify-between pb-3 border-b border-gray-100">
            <h3 class="font-bold text-gray-900 text-sm">Edit Archive Details</h3>
            <button @click="showEditModal = false" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
          </div>
          <div class="mt-4 space-y-3">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Archive Name</label>
              <input
                v-model="editForm.name"
                type="text"
                class="w-full text-xs px-3 py-2 bg-gray-50 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Description</label>
              <textarea
                v-model="editForm.description"
                rows="3"
                class="w-full text-xs px-3 py-2 bg-gray-50 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white resize-none"
              ></textarea>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-2">
            <button
              @click="showEditModal = false"
              class="px-3 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              @click="saveArchiveEdit"
              :disabled="actionLoading"
              class="px-4 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-sm disabled:opacity-50"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>

      <!-- Restore Confirmation Modal -->
      <div
        v-if="showRestoreModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
        @click.self="showRestoreModal = false"
      >
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
          <div class="flex items-center justify-between pb-3 border-b border-gray-100">
            <div class="flex items-center gap-2 font-bold text-gray-900 text-sm">
              <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Restore Reports to Active Root
            </div>
            <button @click="showRestoreModal = false" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
          </div>
          <div class="mt-4 space-y-3">
            <p class="text-xs text-gray-600 leading-relaxed">
              Restore <strong class="text-gray-900">{{ restoreTargetCount }}</strong> report(s) from
              <strong class="text-indigo-600">{{ archiveToRestore?.name }}</strong> back to the active reports directory. They will immediately reappear on your dashboard.
            </p>

            <label class="flex items-center gap-2 p-2.5 rounded-xl bg-gray-50 border border-gray-200 cursor-pointer">
              <input
                v-model="deleteArchiveAfterRestore"
                type="checkbox"
                class="rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
              />
              <span class="text-xs text-gray-700">Delete archive package after restoring</span>
            </label>
          </div>
          <div class="mt-6 flex justify-end gap-2">
            <button
              @click="showRestoreModal = false"
              class="px-3 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              @click="confirmRestore"
              :disabled="actionLoading"
              class="px-4 py-1.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              <span v-if="actionLoading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Restore Now
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
            <h3 class="font-bold text-red-600 text-sm flex items-center gap-2">
              <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Delete Archive
            </h3>
            <button @click="showDeleteModal = false" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
          </div>
          <p class="text-xs text-gray-600 mt-4 leading-relaxed">
            Are you sure you want to permanently delete archive <strong class="text-gray-900">"{{ archiveToDelete?.name }}"</strong>? This will delete the zip archive, index, and metadata from storage. This action cannot be undone.
          </p>
          <div class="mt-6 flex justify-end gap-2">
            <button
              @click="showDeleteModal = false"
              class="px-3 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              @click="confirmDelete"
              :disabled="actionLoading"
              class="px-4 py-1.5 text-xs font-semibold rounded-xl bg-red-600 hover:bg-red-700 text-white transition shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              <span v-if="actionLoading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Delete Permanently
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetch, state } from '../store.js'
import { getApiUrl } from '../utils/url.js'
import ArchivePeakModal from '../components/modals/ArchivePeakModal.vue'

const archives = ref([])
const loading = ref(true)
const actionLoading = ref(false)
const searchQuery = ref('')
const toastMessage = ref('')
const errorMessage = ref('')

// Peaking Modal state
const showPeakModal = ref(false)
const selectedArchiveForPeak = ref(null)

// Edit Modal state
const showEditModal = ref(false)
const archiveToEdit = ref(null)
const editForm = ref({ name: '', description: '' })

// Restore Modal state
const showRestoreModal = ref(false)
const archiveToRestore = ref(null)
const specificReportIdsToRestore = ref(null)
const deleteArchiveAfterRestore = ref(false)

// Delete Modal state
const showDeleteModal = ref(false)
const archiveToDelete = ref(null)

const totalPreservedReports = computed(() => {
  return archives.value.reduce((acc, a) => acc + (a.report_count || 0), 0)
})

const totalStoredSize = computed(() => {
  return archives.value.reduce((acc, a) => acc + (a.size_bytes || 0), 0)
})

const filteredArchives = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return archives.value
  return archives.value.filter(a => {
    const f = a.filters || {}
    const hay = [
      a.name,
      a.description,
      a.id,
      f.search,
      f.subfolder,
      ...(f.tags || []),
      ...(f.protocols || []),
      ...(f.platforms || []),
      ...(f.authors || [])
    ].filter(Boolean).join(' ').toLowerCase()
    return hay.includes(q)
  })
})

const restoreTargetCount = computed(() => {
  if (specificReportIdsToRestore.value?.length) {
    return specificReportIdsToRestore.value.length
  }
  return archiveToRestore.value?.report_count || 0
})

function hasArchiveFilters(arc) {
  const f = arc.filters || {}
  return Boolean(
    f.search ||
    f.subfolder ||
    (f.tags && f.tags.length > 0) ||
    (f.protocols && f.protocols.length > 0) ||
    (f.platforms && f.platforms.length > 0) ||
    (f.authors && f.authors.length > 0)
  )
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return d.toLocaleString()
  } catch {
    return isoStr
  }
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function showToast(msg) {
  toastMessage.value = msg
  setTimeout(() => {
    if (toastMessage.value === msg) {
      toastMessage.value = ''
    }
  }, 4000)
}

async function loadArchives() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await apiFetch('/api/archives')
    if (!res.ok) {
      throw new Error(`Failed to load archives (${res.status})`)
    }
    archives.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

function openPeakModal(arc) {
  selectedArchiveForPeak.value = arc
  showPeakModal.value = true
}

function downloadArchive(arc) {
  const path = `/api/archives/${encodeURIComponent(arc.id)}/download`
  const downloadUrl = getApiUrl(path, state.activeServer)
  const a = document.createElement('a')
  a.href = downloadUrl
  a.download = `${arc.name || arc.id}.zip`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  showToast(`Downloading "${arc.name}.zip"...`)
}

function openEditModal(arc) {
  archiveToEdit.value = arc
  editForm.value = {
    name: arc.name || '',
    description: arc.description || ''
  }
  showEditModal.value = true
}

async function saveArchiveEdit() {
  if (!archiveToEdit.value?.id) return
  actionLoading.value = true
  try {
    const res = await apiFetch(`/api/archives/${encodeURIComponent(archiveToEdit.value.id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: editForm.value.name,
        description: editForm.value.description
      })
    })
    if (!res.ok) throw new Error('Failed to update archive')
    const updated = await res.json()
    const idx = archives.value.findIndex(a => a.id === updated.id)
    if (idx >= 0) archives.value[idx] = updated
    showEditModal.value = false
    showToast(`Archive "${updated.name}" updated`)
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    actionLoading.value = false
  }
}

function openRestoreModal(arc, reportIds = null) {
  archiveToRestore.value = arc
  specificReportIdsToRestore.value = reportIds
  deleteArchiveAfterRestore.value = false
  showRestoreModal.value = true
}

function handleRestoreSelectedFromPeak(selectedIds) {
  showPeakModal.value = false
  openRestoreModal(selectedArchiveForPeak.value, selectedIds)
}

function handleRestoreAllFromPeak() {
  showPeakModal.value = false
  openRestoreModal(selectedArchiveForPeak.value, null)
}

async function confirmRestore() {
  if (!archiveToRestore.value?.id) return
  actionLoading.value = true
  try {
    const res = await apiFetch(`/api/archives/${encodeURIComponent(archiveToRestore.value.id)}/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report_ids: specificReportIdsToRestore.value || null,
        delete_after_restore: deleteArchiveAfterRestore.value
      })
    })
    if (!res.ok) throw new Error('Failed to restore archive')
    const result = await res.json()
    showRestoreModal.value = false
    showToast(`Restored ${result.restored_count} report(s) back to active dashboard`)
    if (result.archive_deleted) {
      archives.value = archives.value.filter(a => a.id !== archiveToRestore.value.id)
    }
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    actionLoading.value = false
  }
}

function openDeleteModal(arc) {
  archiveToDelete.value = arc
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (!archiveToDelete.value?.id) return
  actionLoading.value = true
  try {
    const res = await apiFetch(`/api/archives/${encodeURIComponent(archiveToDelete.value.id)}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to delete archive')
    archives.value = archives.value.filter(a => a.id !== archiveToDelete.value.id)
    showDeleteModal.value = false
    showToast('Archive deleted permanently')
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  loadArchives()
})
</script>
