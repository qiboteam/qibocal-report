<template>
  <div class="min-h-screen bg-[#f7f7f7] text-[#000000] flex flex-col">
    <header class="sticky top-0 z-20 bg-[#f7f7f7]/85 backdrop-blur border-b border-gray-200/60">
      <!--
        Nothing but the mark: the sections, the dashboard included, are one
        Go menu away, with their accelerators, and the home page lists them
        again with the figures a navigation bar cannot show.
      -->
      <div class="max-w-5xl mx-auto px-5 h-14 flex items-center">
        <router-link to="/" class="lx-logo" title="Qibocal home" aria-label="Qibocal home">
          <launcher-logo />
        </router-link>
      </div>
    </header>

    <!-- Room for the status bar, so nothing hides behind it. -->
    <main class="flex-1 w-full pb-8">
      <router-view />
    </main>

    <!--
      The status bar: the page's own colour, no edge, always on top, so it
      blends into a page that fits the window and sits over one that does
      not. The command line's version on the left; on the right, the latest
      thing said, fading by itself, and the count of everything said, which
      opens the list. An installation in progress sits between the two for
      as long as it runs, with the way to its output.
    -->
    <footer class="lx-status" role="status" aria-live="polite">
      <div class="px-5 h-full flex items-center gap-5">
        <router-link to="/settings" class="inline-flex items-center gap-2 truncate shrink-0 max-w-[40%]" :title="versionTitle">
          <span class="lx-dot" :class="dotClass" />
          <span class="truncate">{{ versionLabel }}</span>
        </router-link>

        <router-link
          v-if="installing"
          to="/processes"
          class="inline-flex items-center gap-1.5 shrink-0"
          title="Follow the installation in Running"
        >
          <Loader2 class="w-3 h-3 lx-spin" />
          Installing qibocal-report… follow it in Running
        </router-link>

        <div ref="corner" class="ml-auto flex items-center gap-2 min-w-0 relative">
          <!-- The latest message, leading to the section it is about when it has one. -->
          <component
            :is="state.message?.link ? 'router-link' : 'span'"
            v-if="state.message"
            :to="state.message.link || undefined"
            class="truncate"
            :class="state.message.kind === 'error' ? 'lx-status-error' : ''"
            :title="state.message.text"
          >{{ state.message.text }}</component>

          <button
            v-if="inbox.length"
            type="button"
            class="lx-count"
            :class="{ 'is-open': open }"
            :title="`${inbox.length} notification${inbox.length === 1 ? '' : 's'}`"
            :aria-expanded="open"
            @click="open = !open"
          >
            <Bell class="w-3 h-3" />
            <span class="lx-count-badge">{{ inbox.length }}</span>
          </button>

          <!--
            The five most recent, each the way to its section — the whole
            row but the time and the cross, which archives it. The title and
            "More" open the page with everything.
          -->
          <div v-if="open && inbox.length" class="lx-notices" role="list">
            <!-- Nothing from the last day: the page has the older ones. -->
            <div class="lx-notices-head">
              <router-link to="/notifications" class="hover:text-[#3b107e] transition" title="All notifications" @click="open = false">
                Notifications
              </router-link>
              <button type="button" class="hover:text-[#3b107e] transition" title="Archive all" @click="archiveEverything">Archive all</button>
            </div>
            <div
              v-for="entry in recent"
              :key="entry.id"
              class="lx-notice"
              :class="{ 'is-error': entry.kind === 'error' }"
              role="listitem"
            >
              <span class="lx-notice-time">{{ time(entry.at) }}</span>
              <component
                :is="entry.link ? 'router-link' : 'span'"
                :to="entry.link || undefined"
                class="lx-notice-text"
                :class="{ 'is-link': entry.link }"
                :title="entry.link ? `Go to ${sectionTitle(entry.link)}` : undefined"
                @click="entry.link && (open = false)"
              >{{ entry.text }}</component>
              <button type="button" class="lx-notice-close" :aria-label="`Archive: ${entry.text}`" title="Archive" @click="archiveNotification(entry.id)">
                <X class="w-3 h-3" />
              </button>
            </div>
            <router-link v-if="inbox.length > recent.length" to="/notifications" class="lx-notices-more" @click="open = false">
              {{ recent.length ? `${inbox.length - recent.length} more…` : `${inbox.length} older…` }}
            </router-link>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Loader2, X } from 'lucide-vue-next'
import LauncherLogo from './components/LauncherLogo.vue'
import { installMenu } from './menu.js'
import { sections } from './router.js'
import {
  state,
  archiveAll,
  archiveNotification,
  fail,
  hasQibocal,
  inbox,
  initialize,
  installing,
  launchOptionsFor,
  openDashboard,
  startServer
} from './state.js'
import { describeSpec } from './lib/versions.js'
import { isRecent } from './lib/time.js'

/** How many entries the bubble shows; the page has them all. */
const RECENT = 5

const router = useRouter()
const open = ref(false)
const corner = ref(null)

/** What the command line says of itself, with the version the launcher put there. */
const versionLabel = computed(() => {
  const environment = state.environment
  if (!environment) return ''
  if (!hasQibocal.value) return installing.value ? 'qibocal-report: installing' : 'qibocal-report not installed'
  const version = String(environment.version || '').replace(/^qibocal,?\s*version\s*/i, '').trim()
  const held = environment.source === 'managed' && environment.managedPackage
    ? describeSpec(environment.managedPackage, environment)
    : ''
  return `qibocal-report ${version || ''}${held ? ` · ${held}` : ''}`.replace(/\s+/g, ' ').trim()
})
const versionTitle = computed(() => state.environment?.executable || 'Configuration')
/** Found, being installed, or missing: green, amber, red. */
const dotClass = computed(() =>
  hasQibocal.value ? 'bg-emerald-500' : installing.value ? 'bg-amber-400' : 'bg-red-400'
)

/** The title of the section a notification points at. */
function sectionTitle(link) {
  return sections.find(section => section.name === link?.name)?.title || 'the section'
}

function time(at) {
  return new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/** The five most recent of the last day; the page has the rest. */
const now = ref(Date.now())
const recent = computed(() => inbox.value.filter(entry => isRecent(entry.at, now.value)).slice(0, RECENT))
watch(open, opened => {
  if (opened) now.value = Date.now()
})

function archiveEverything() {
  archiveAll()
  open.value = false
}

/** A click anywhere else, or the window losing focus, closes the list. */
function closeFromOutside(event) {
  if (!open.value) return
  if (event?.type === 'pointerdown' && corner.value?.contains(event.target)) return
  open.value = false
}

/**
 * Bring a registered server up, as it was started last time or at its
 * registered address on this machine; one that is neither opens its form.
 */
async function launchServer(server) {
  const options = launchOptionsFor(server)
  if (!options) {
    router.push({ name: 'servers', query: { server: server.id } })
    return
  }
  try {
    await startServer(options, { url: server.url })
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error, 'servers')
  }
}

function refreshMenu() {
  installMenu({
    goTo: name => router.push({ name }),
    openDashboard,
    launchServer,
    servers: state.servers
  })
}

onMounted(async () => {
  document.addEventListener('pointerdown', closeFromOutside)
  window.addEventListener('blur', closeFromOutside)
  await initialize()
  refreshMenu()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', closeFromOutside)
  window.removeEventListener('blur', closeFromOutside)
})

watch(() => state.servers.map(server => `${server.id}:${server.name}`).join('|'), refreshMenu)
// The list closes with its last entry, and when leaving the page.
watch(() => inbox.value.length, count => {
  if (!count) open.value = false
})
watch(() => router.currentRoute.value.fullPath, () => {
  open.value = false
})
</script>
