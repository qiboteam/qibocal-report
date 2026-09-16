<template>
  <div class="min-h-screen bg-[#f7f7f7] py-8 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto">
      <!-- Top Navigation -->
      <div class="flex items-center justify-between pb-6 border-b border-gray-200">
        <router-link 
          to="/dashboard"
          class="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-[#833dff] transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </router-link>

        <a 
          href="/api/docs/swagger" 
          target="_blank"
          class="inline-flex items-center gap-1 text-xs font-semibold text-[#833dff] hover:underline"
        >
          Interactive Swagger UI ↗
        </a>
      </div>

      <!-- Header -->
      <div class="my-6">
        <h1 class="text-3xl font-bold text-gray-900">
          Documentation
        </h1>
        <p class="text-xs text-gray-500 mt-1">
          Complete usage guidelines, architectural decisions, and REST API specification.
        </p>

        <!-- Document Tabs (Issue #12) -->
        <div class="flex items-center gap-2 mt-4 border-b border-gray-200 pb-2">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            @click="activeTab = tab.id; loadDoc(tab.id)"
            class="px-4 py-2 rounded-xl text-xs font-semibold transition"
            :class="activeTab === tab.id ? 'bg-[#833dff] text-white shadow-xs' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'"
          >
            {{ tab.title }}
          </button>
        </div>
      </div>

      <!-- Markdown Viewer Container -->
      <div class="bm-card p-6 sm:p-10 border border-gray-100">
        <div v-if="loading" class="text-center py-12 text-xs text-gray-400">
          Loading documentation...
        </div>
        <article 
          v-else 
          class="prose prose-purple max-w-none text-sm text-gray-800 leading-relaxed"
          v-html="renderedContent"
        ></article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'

const tabs = [
  { id: 'usage', title: 'User Guide' },
  { id: 'developer', title: 'Developer & Design' },
  { id: 'api', title: 'REST API' }
]

const activeTab = ref('usage')
const rawMarkdown = ref('')
const loading = ref(true)

const renderedContent = computed(() => {
  return marked(rawMarkdown.value)
})

onMounted(() => {
  loadDoc(activeTab.value)
})

async function loadDoc(name) {
  loading.value = true
  try {
    const res = await fetch(`/api/docs-content/${name}`)
    if (res.ok) {
      rawMarkdown.value = await res.text()
    } else {
      rawMarkdown.value = `# Not Found\nCould not load documentation for ${name}.`
    }
  } catch (err) {
    rawMarkdown.value = `# Error\nFailed to fetch documentation.`
  } finally {
    loading.value = false
  }
}
</script>

<style>
/* Markdown styling inside docs */
article h1 {
  font-size: 1.8rem;
  font-family: Georgia, Cambria, "Times New Roman", Times, serif;
  font-weight: 700;
  margin-top: 1rem;
  margin-bottom: 1rem;
  color: #111827;
}

article h2 {
  font-size: 1.3rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #1f2937;
  border-bottom: 1px solid #f3f4f6;
  padding-bottom: 0.3rem;
}

article h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: #374151;
}

article p {
  margin-bottom: 1rem;
  color: #4b5563;
}

article pre {
  background: #1e1e2e;
  color: #f8f8f2;
  padding: 1rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  font-size: 0.8rem;
  font-family: monospace;
  margin: 1rem 0;
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
  margin-bottom: 0.25rem;
}
</style>
