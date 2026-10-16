import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '../store.js'
import { DEFAULT_DOCS_NAV } from '../utils/docsNav.js'

export { DEFAULT_DOCS_NAV }

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
