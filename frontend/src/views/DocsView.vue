<template>
  <div class="min-h-screen bg-[#f7f7f7] py-6 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto">
      <!-- Top Bar Navigation -->
      <div class="flex items-center justify-between pb-4 mb-6 border-b border-gray-200">
        <router-link
          to="/dashboard"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-[#833dff] transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </router-link>

        <div class="flex items-center gap-4">
          <a
            href="https://qibo.science"
            target="_blank"
            rel="noopener noreferrer"
            class="hidden sm:inline-flex items-center gap-1 text-xs font-semibold text-gray-600 hover:text-[#833dff] transition"
          >
            qibo.science ↗
          </a>
          <a
            :href="swaggerUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 text-xs font-semibold text-[#833dff] hover:underline"
          >
            Interactive Swagger UI ↗
          </a>
        </div>
      </div>

      <!-- Main Layout: Sidebar Navigation + Article Content -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <!-- Documentation Sidebar Navigation -->
        <docs-sidebar
          class="lg:col-span-3"
          :nav="nav"
          :active-doc="activeDoc"
          @select="navigateTo"
        />

        <!-- Markdown Document Viewer -->
        <main class="lg:col-span-9 space-y-6">
          <div class="bm-card p-6 sm:p-10 border border-gray-100 bg-white rounded-2xl shadow-xs">
            <!-- Breadcrumbs Navigation Menu -->
            <docs-breadcrumb
              :nav="nav"
              :current-section="currentSection"
              :current-title="currentTitle"
              :active-doc="activeDoc"
              :is-section-page="isSectionPage"
              @navigate="navigateTo"
            />

            <!-- Loading State -->
            <div v-if="loading" class="flex flex-col items-center justify-center py-24 text-gray-400">
              <svg class="animate-spin h-8 w-8 text-[#833dff] mb-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span class="text-xs">Loading documentation...</span>
            </div>

            <!-- Article Content -->
            <article
              v-else
              class="prose prose-purple max-w-none text-sm text-gray-800 leading-relaxed"
              v-html="renderedContent"
              @click="onArticleClick"
            ></article>

            <!-- Bottom Prev / Next Navigation -->
            <div v-if="!loading" class="mt-12 pt-6 border-t border-gray-200 flex items-center justify-between gap-4">
              <div>
                <button
                  v-if="prevDoc"
                  @click="navigateTo(prevDoc.path)"
                  class="flex flex-col items-start px-4 py-2.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 text-left transition group cursor-pointer"
                >
                  <span class="text-[10px] uppercase font-bold text-gray-400 group-hover:text-[#833dff]">← Previous</span>
                  <span class="text-xs font-semibold text-gray-800 group-hover:text-[#833dff]">{{ prevDoc.title }}</span>
                </button>
              </div>
              <div>
                <button
                  v-if="nextDoc"
                  @click="navigateTo(nextDoc.path)"
                  class="flex flex-col items-end px-4 py-2.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/50 text-right transition group cursor-pointer"
                >
                  <span class="text-[10px] uppercase font-bold text-gray-400 group-hover:text-[#833dff]">Next →</span>
                  <span class="text-xs font-semibold text-gray-800 group-hover:text-[#833dff]">{{ nextDoc.title }}</span>
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import { getActiveServerUrl } from '../store.js'
import { useDocs } from '../composables/useDocs.js'
import DocsSidebar from '../components/docs/DocsSidebar.vue'
import DocsBreadcrumb from '../components/docs/DocsBreadcrumb.vue'

const {
  nav,
  activeDoc,
  rawMarkdown,
  loading,
  currentSection,
  currentTitle,
  isSectionPage,
  prevDoc,
  nextDoc,
  navigateTo
} = useDocs()

const swaggerUrl = computed(() => {
  const base = getActiveServerUrl()
  return base ? `${base}/api/docs/swagger` : '/api/docs/swagger'
})

const renderedContent = computed(() => {
  return marked(rawMarkdown.value)
})

function onArticleClick(e) {
  const target = e.target.closest('a')
  if (!target) return
  const href = target.getAttribute('href')
  if (!href || href.startsWith('#')) return
  if (
    href.startsWith('http://') ||
    href.startsWith('https://') ||
    href.startsWith('//') ||
    href.startsWith('mailto:')
  ) {
    target.setAttribute('target', '_blank')
    target.setAttribute('rel', 'noopener noreferrer')
    return
  }
  // Internal doc link
  e.preventDefault()
  let docPath = href.replace(/^\/+/, '').replace(/^docs\//, '').replace(/\.md$/, '')
  if (!docPath.includes('/') && currentSection.value) {
    const sec = nav.value.find(s => s.section === currentSection.value)
    if (sec?.path && sec.path !== 'index') {
      docPath = `${sec.path}/${docPath}`
    }
  }
  navigateTo(docPath)
}
</script>

<style>
/* Markdown styling inside docs */
article h1 {
  font-size: 1.8rem;
  font-family: Georgia, Cambria, "Times New Roman", Times, serif;
  font-weight: 700;
  margin-top: 0.5rem;
  margin-bottom: 1rem;
  color: #111827;
}

article h2 {
  font-size: 1.3rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  color: #1f2937;
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 0.3rem;
}

article h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  color: #374151;
}

article p {
  margin-bottom: 1rem;
  color: #4b5563;
  line-height: 1.65;
}

article blockquote {
  border-left: 3px solid #833dff;
  background: #fbf9ff;
  padding: 0.75rem 1rem;
  margin: 1rem 0;
  border-radius: 0 0.5rem 0.5rem 0;
  color: #4b5563;
}

article pre {
  background: #1e1e2e;
  color: #f8f8f2;
  padding: 1rem 1.25rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  font-size: 0.8rem;
  font-family: monospace;
  margin: 1.25rem 0;
}

article code {
  background: #f3f0ff;
  color: #833dff;
  padding: 0.15rem 0.35rem;
  border-radius: 0.25rem;
  font-size: 0.85em;
  font-family: monospace;
}

article pre code {
  background: transparent;
  color: inherit;
  padding: 0;
}

article ul, article ol {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

article li {
  margin-bottom: 0.35rem;
}

article table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.85rem;
}

article th, article td {
  border: 1px solid #e5e7eb;
  padding: 0.6rem 0.85rem;
  text-align: left;
}

article th {
  background: #faf5ff;
  color: #581c87;
  font-weight: 600;
}

article tr:nth-child(even) {
  background: #fafafa;
}

article a {
  color: #833dff;
  text-decoration: underline;
  text-underline-offset: 2px;
}

article a:hover {
  color: #6b21a8;
}

article hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 2rem 0;
}
</style>
