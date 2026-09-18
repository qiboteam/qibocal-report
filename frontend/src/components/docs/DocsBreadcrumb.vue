<template>
  <nav aria-label="Breadcrumbs" class="flex flex-wrap items-center gap-1.5 text-xs text-gray-500 mb-6 pb-4 border-b border-gray-100">
    <!-- Root 'Docs' segment -->
    <div class="relative inline-flex items-center" ref="docsMenuRef">
      <button
        type="button"
        @click="$emit('navigate', 'index')"
        class="inline-flex items-center gap-1.5 font-medium text-gray-500 hover:text-[#833dff] transition rounded-lg px-2 py-1 hover:bg-gray-100 cursor-pointer"
        title="Overview & Ecosystem"
      >
        <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <span>Docs</span>
      </button>

      <button
        type="button"
        @click.stop="toggleDocsMenu"
        class="p-1 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition cursor-pointer"
        title="Browse documentation sections"
      >
        <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': isDocsMenuOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <!-- Docs Dropdown Menu -->
      <div
        v-if="isDocsMenuOpen"
        class="absolute left-0 top-full mt-1.5 w-64 rounded-xl bg-white shadow-xl border border-gray-200 py-1.5 z-40 animate-fade-in"
      >
        <div class="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-100 mb-1">
          Documentation Sections
        </div>
        <button
          v-for="s in nav"
          :key="s.section"
          type="button"
          @click="selectSection(s)"
          class="w-full text-left px-3 py-2 text-xs transition flex items-center justify-between cursor-pointer group"
          :class="currentSection === s.section ? 'bg-purple-50 text-[#833dff] font-semibold' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
        >
          <span class="truncate">{{ s.section }}</span>
          <span class="text-[10px] font-mono text-gray-400 group-hover:text-purple-600">{{ s.items.length }} {{ s.items.length === 1 ? 'doc' : 'docs' }}</span>
        </button>
      </div>
    </div>

    <!-- Separator -->
    <span class="text-gray-300">/</span>

    <!-- Section segment (if present and not root overview) -->
    <template v-if="currentSection && currentSection !== 'Overview'">
      <div class="relative inline-flex items-center" ref="sectionMenuRef">
        <!-- Links to SECTION PAGE (Table of Contents), NOT first page! -->
        <button
          type="button"
          @click="navigateToSectionPage"
          class="inline-flex items-center font-medium transition rounded-lg px-2 py-1 hover:bg-gray-100 cursor-pointer"
          :class="isSectionPage ? 'text-gray-900 font-semibold' : 'text-gray-600 hover:text-[#833dff]'"
          :title="`Go to ${currentSection} table of contents`"
        >
          <span>{{ currentSection }}</span>
        </button>

        <button
          type="button"
          @click.stop="toggleSectionMenu"
          class="p-1 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition cursor-pointer"
          title="Browse pages in this section"
        >
          <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': isSectionMenuOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Section Dropdown Menu -->
        <div
          v-if="isSectionMenuOpen"
          class="absolute left-0 top-full mt-1.5 w-72 rounded-xl bg-white shadow-xl border border-gray-200 py-1.5 z-40 animate-fade-in"
        >
          <div class="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-100 mb-1 flex items-center justify-between">
            <span>{{ currentSection }}</span>
            <button
              type="button"
              @click="navigateToSectionPage"
              class="text-[10px] text-[#833dff] hover:underline font-normal cursor-pointer"
            >
              Overview
            </button>
          </div>
          <button
            v-for="item in currentSectionItems"
            :key="item.path"
            type="button"
            @click="selectItem(item.path)"
            class="w-full text-left px-3 py-2 text-xs transition flex items-center justify-between cursor-pointer group"
            :class="activeDoc === item.path ? 'bg-purple-50 text-[#833dff] font-semibold' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'"
          >
            <span class="truncate">{{ item.title }}</span>
            <span v-if="activeDoc === item.path" class="w-1.5 h-1.5 rounded-full bg-[#833dff] ml-2 shrink-0"></span>
          </button>
        </div>
      </div>

      <!-- Subpage Title (only when not on section page itself) -->
      <template v-if="!isSectionPage && currentTitle && currentTitle !== currentSection">
        <span class="text-gray-300">/</span>
        <span class="text-gray-900 font-semibold truncate px-1">{{ currentTitle }}</span>
      </template>
    </template>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  nav: {
    type: Array,
    required: true
  },
  currentSection: {
    type: String,
    default: ''
  },
  currentTitle: {
    type: String,
    required: true
  },
  activeDoc: {
    type: String,
    required: true
  },
  isSectionPage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['navigate'])

const isDocsMenuOpen = ref(false)
const isSectionMenuOpen = ref(false)
const docsMenuRef = ref(null)
const sectionMenuRef = ref(null)

const currentSectionItems = computed(() => {
  if (!props.currentSection) return []
  const sec = props.nav.find(s => s.section === props.currentSection)
  return sec?.items || []
})

function toggleDocsMenu() {
  isDocsMenuOpen.value = !isDocsMenuOpen.value
  if (isDocsMenuOpen.value) isSectionMenuOpen.value = false
}

function toggleSectionMenu() {
  isSectionMenuOpen.value = !isSectionMenuOpen.value
  if (isSectionMenuOpen.value) isDocsMenuOpen.value = false
}

function selectSection(sec) {
  isDocsMenuOpen.value = false
  if (sec?.path) {
    emit('navigate', sec.path)
  } else if (sec?.items?.length) {
    emit('navigate', sec.items[0].path)
  }
}

function navigateToSectionPage() {
  isSectionMenuOpen.value = false
  const sec = props.nav.find(s => s.section === props.currentSection)
  if (sec?.path) {
    emit('navigate', sec.path)
  }
}

function selectItem(path) {
  isSectionMenuOpen.value = false
  emit('navigate', path)
}

function onClickOutside(e) {
  if (docsMenuRef.value && !docsMenuRef.value.contains(e.target)) {
    isDocsMenuOpen.value = false
  }
  if (sectionMenuRef.value && !sectionMenuRef.value.contains(e.target)) {
    isSectionMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>
