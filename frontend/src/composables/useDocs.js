import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../store.js'

export const DEFAULT_DOCS_NAV = [
  {
    section: 'Overview',
    path: 'index',
    items: [
      {
        id: 'index',
        path: 'index',
        title: 'Overview & Ecosystem',
        description: 'Introduction to Qibo ecosystem, projects, and qibocal-report architecture'
      }
    ]
  },
  {
    section: 'User Guide',
    path: 'user-guide',
    items: [
      {
        id: 'user-guide/quickstart',
        path: 'user-guide/quickstart',
        title: 'Getting Started & Quickstart',
        description: 'Installation, CLI commands, and report directory structure'
      },
      {
        id: 'user-guide/dashboard',
        path: 'user-guide/dashboard',
        title: 'Dashboard & Server Management',
        description: 'Managing servers, search, smart facets, dual views, and bulk actions'
      },
      {
        id: 'user-guide/reports',
        path: 'user-guide/reports',
        title: 'Reports, Protocols & Exports',
        description: 'Interactive charts, protocol timings, downloads, and PDF printing'
      }
    ]
  },
  {
    section: 'Developer & Architecture',
    path: 'developer',
    items: [
      {
        id: 'developer/architecture',
        path: 'developer/architecture',
        title: 'System Architecture',
        description: 'FastAPI backend, Vue 3 SPA frontend, and execution modes'
      },
      {
        id: 'developer/workflow',
        path: 'developer/workflow',
        title: 'Development Workflow',
        description: 'devenv environment, live Vite HMR, testing, and packaging'
      },
      {
        id: 'developer/design-system',
        path: 'developer/design-system',
        title: 'Design System & Aesthetics',
        description: 'BackMarket design palette, typography, and print media CSS'
      }
    ]
  },
  {
    section: 'Reference',
    path: 'reference',
    items: [
      {
        id: 'reference/cli',
        path: 'reference/cli',
        title: 'CLI Reference',
        description: 'Complete command line options and environment variables'
      },
      {
        id: 'reference/api',
        path: 'reference/api',
        title: 'REST API & WebSockets',
        description: 'REST endpoints specification, schemas, and WebSocket events'
      }
    ]
  }
]

const bundledDocs = import.meta.glob('../../../docs/**/*.md', { query: '?raw', import: 'default', eager: true })

function getBundledDocContent(name) {
  const cleanName = (name || '').replace(/^\/+/, '').replace(/\.md$/, '')
  for (const [key, content] of Object.entries(bundledDocs)) {
    const normKey = key
      .replace(/^(\.\.\/)+docs\//, '')
      .replace(/\.md$/, '')
    if (
      normKey === cleanName ||
      normKey === `${cleanName}/index` ||
      (cleanName.endsWith('/index') && normKey === cleanName.replace(/\/index$/, ''))
    ) {
      return content
    }
  }
  return null
}

export function useDocs() {
  const route = useRoute()
  const router = useRouter()

  const nav = ref(DEFAULT_DOCS_NAV)
  const activeDoc = ref('index')
  const rawMarkdown = ref('')
  const loading = ref(true)

  const flatNavItems = computed(() => {
    const items = []
    for (const s of nav.value) {
      if (s.path && s.path !== 'index') {
        items.push({
          id: s.path,
          path: s.path,
          title: s.section,
          description: `${s.section} table of contents`,
          sectionName: s.section,
          isSection: true
        })
      }
      for (const item of s.items) {
        items.push({ ...item, sectionName: s.section, isSection: false })
      }
    }
    return items
  })

  const currentItem = computed(() => {
    return flatNavItems.value.find(i => i.path === activeDoc.value)
  })

  const currentSection = computed(() => {
    if (currentItem.value) return currentItem.value.sectionName
    const matchingSection = nav.value.find(s =>
      s.path === activeDoc.value || activeDoc.value.startsWith(`${s.path}/`)
    )
    return matchingSection?.section || ''
  })

  const isSectionPage = computed(() => {
    const sec = nav.value.find(s => s.section === currentSection.value)
    return Boolean(sec && (activeDoc.value === sec.path || activeDoc.value === `${sec.path}/index`))
  })

  const currentTitle = computed(() => {
    if (isSectionPage.value) return currentSection.value
    return currentItem.value?.title || activeDoc.value
  })

  const currentDocIndex = computed(() => {
    return flatNavItems.value.findIndex(i => i.path === activeDoc.value)
  })

  const prevDoc = computed(() => {
    const idx = currentDocIndex.value
    return idx > 0 ? flatNavItems.value[idx - 1] : null
  })

  const nextDoc = computed(() => {
    const idx = currentDocIndex.value
    return (idx >= 0 && idx < flatNavItems.value.length - 1)
      ? flatNavItems.value[idx + 1]
      : null
  })

  function syncDocFromRoute() {
    const pageParam = route.params.page
    const target = (typeof pageParam === 'string' && pageParam.trim())
      ? pageParam.trim().replace(/^\/+/, '').replace(/\.md$/, '')
      : 'index'
    activeDoc.value = target
    loadDoc(target)
  }

  function navigateTo(path) {
    const clean = path.replace(/^\/+/, '').replace(/\.md$/, '')
    if (clean === 'index') {
      router.push('/docs')
    } else {
      router.push(`/docs/${clean}`)
    }
  }

  async function fetchNav() {
    try {
      const res = await apiFetch('/api/docs-nav')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          nav.value = data
        }
      }
    } catch (err) {
      console.debug('Using client-side default docs nav', err)
    }
  }

  async function loadDoc(name) {
    loading.value = true
    try {
      const res = await apiFetch(`/api/docs-content/${name}`)
      if (res.ok) {
        rawMarkdown.value = await res.text()
        loading.value = false
        return
      }
    } catch (err) {
      console.warn('Failed to load docs from active server, trying local host...', err)
    }

    try {
      const localRes = await fetch(`/api/docs-content/${name}`)
      if (localRes.ok) {
        rawMarkdown.value = await localRes.text()
        loading.value = false
        return
      }
    } catch {}

    const fallback = getBundledDocContent(name)
    if (fallback) {
      rawMarkdown.value = fallback
      loading.value = false
      return
    }

    rawMarkdown.value = `# Not Found\nCould not load documentation for \`${name}\`.`
    loading.value = false
  }

  onMounted(async () => {
    await fetchNav()
    syncDocFromRoute()
  })

  watch(
    () => route.params.page,
    () => {
      syncDocFromRoute()
    }
  )

  return {
    nav,
    activeDoc,
    rawMarkdown,
    loading,
    currentSection,
    currentTitle,
    isSectionPage,
    prevDoc,
    nextDoc,
    navigateTo,
    loadDoc
  }
}
