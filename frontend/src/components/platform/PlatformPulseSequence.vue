<template>
  <div class="pulse-sequence-card rounded-2xl bg-white border border-purple-150 shadow-2xs overflow-hidden">
    <!-- Sequence Header -->
    <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-gradient-to-r from-purple-50/60 to-indigo-50/40 border-b border-purple-100">
      <div class="flex items-center gap-2.5">
        <span class="w-2.5 h-2.5 rounded-full bg-[#833dff]"></span>
        <span class="font-mono text-sm font-bold text-gray-900 tracking-tight">
          {{ gateName }}
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-mono font-semibold">
          {{ totalDuration }} ns
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-mono">
          {{ channelTracks.length }} {{ channelTracks.length === 1 ? 'channel' : 'channels' }}
        </span>
        <span class="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-mono">
          {{ sequence.length }} {{ sequence.length === 1 ? 'event' : 'events' }}
        </span>
      </div>

      <!-- Copy Full Sequence JSON -->
      <button
        type="button"
        @click="copySequenceJson"
        class="px-2.5 py-1 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold inline-flex items-center gap-1.5 transition cursor-pointer"
        title="Copy raw pulse sequence JSON"
      >
        <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <span>{{ copyStatusText }}</span>
      </button>
    </div>

    <!-- Multi-Channel Timeline Tracks Area -->
    <div class="p-4 sm:p-5 overflow-x-auto">
      <div class="min-w-[560px]">
        <!-- Timeline Time Ruler / Axis -->
        <div class="flex items-center mb-3 text-[10px] font-mono text-gray-400 pl-32 pr-2">
          <div class="flex-1 flex justify-between items-center relative h-5 border-b border-gray-200">
            <span class="relative -bottom-1 font-semibold text-gray-500">0 ns</span>
            <span v-for="tick in timeTicks" :key="tick" class="relative -bottom-1">
              {{ tick }} ns
            </span>
            <span class="relative -bottom-1 font-semibold text-purple-700">{{ totalDuration }} ns</span>
          </div>
        </div>

        <!-- Channel Tracks -->
        <div class="space-y-3">
          <div
            v-for="track in channelTracks"
            :key="track.channel"
            class="flex items-center gap-3 group/track"
          >
            <!-- Channel Label Column -->
            <div class="w-32 shrink-0 flex items-center justify-between gap-1.5 pr-2">
              <span
                class="px-2 py-0.5 rounded-lg text-[11px] font-mono font-bold truncate shrink-0"
                :class="getChannelTagClass(track.channel)"
                :title="track.channel"
              >
                {{ track.channel }}
              </span>
              <span class="text-[9px] text-gray-400 font-mono">
                {{ track.events.length }}
              </span>
            </div>

            <!-- Track Lane (with baseline and event pulses) -->
            <div class="flex-1 relative h-14 bg-slate-50/80 rounded-xl border border-gray-150 overflow-hidden shadow-2xs">
              <!-- Grid Ticks (vertical guide lines) -->
              <div
                v-for="tickPercent in tickPercents"
                :key="tickPercent"
                class="absolute top-0 bottom-0 border-l border-dashed border-gray-200 pointer-events-none"
                :style="{ left: `${tickPercent}%` }"
              ></div>

              <!-- Channel Center Baseline -->
              <div class="absolute left-0 right-0 top-1/2 -translate-y-1/2 border-b border-gray-200 pointer-events-none"></div>

              <!-- Events on Track -->
              <div
                v-for="ev in track.events"
                :key="ev.id"
                @click="selectEvent(ev)"
                class="absolute top-1 bottom-1 flex items-center cursor-pointer transition-transform hover:scale-[1.01] select-none"
                :style="getEventStyle(ev)"
              >
                <!-- 1. DRAG or Gaussian Pulse -->
                <div
                  v-if="ev.kind === 'pulse' && isSmoothEnvelope(ev)"
                  class="w-full h-full relative flex items-center justify-center rounded-lg overflow-hidden group/pulse"
                  :class="selectedEvent?.id === ev.id ? 'ring-2 ring-[#833dff]' : ''"
                  :title="getEventTooltip(ev)"
                >
                  <svg viewBox="0 0 100 40" preserveAspectRatio="none" class="w-full h-full">
                    <defs>
                      <linearGradient :id="'drag-' + ev.id" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#833dff" stop-opacity="0.85" />
                        <stop offset="100%" stop-color="#c084fc" stop-opacity="0.25" />
                      </linearGradient>
                    </defs>
                    <path d="M 0,38 C 20,38 30,4 50,4 C 70,4 80,38 100,38 Z" :fill="'url(#drag-' + ev.id + ')'" stroke="#833dff" stroke-width="1.5" />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none px-1">
                    <span class="text-[10px] font-mono font-bold text-white drop-shadow-sm truncate">
                      {{ ev.event.envelope?.kind?.toUpperCase() || 'DRAG' }}
                    </span>
                    <span class="text-[9px] font-mono text-purple-100 drop-shadow-sm truncate">
                      {{ ev.duration }}ns · a:{{ formatAmp(ev.event.amplitude) }}
                    </span>
                  </div>
                </div>

                <!-- 2. Rectangular Pulse -->
                <div
                  v-else-if="ev.kind === 'pulse' && isRectangularEnvelope(ev)"
                  class="w-full h-full relative flex items-center justify-center rounded-lg overflow-hidden"
                  :class="selectedEvent?.id === ev.id ? 'ring-2 ring-cyan-500' : ''"
                  :title="getEventTooltip(ev)"
                >
                  <svg viewBox="0 0 100 40" preserveAspectRatio="none" class="w-full h-full">
                    <defs>
                      <linearGradient :id="'rect-' + ev.id" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.85" />
                        <stop offset="100%" stop-color="#67e8f9" stop-opacity="0.25" />
                      </linearGradient>
                    </defs>
                    <rect x="1" y="4" width="98" height="34" rx="3" :fill="'url(#rect-' + ev.id + ')'" stroke="#0891b2" stroke-width="1.5" />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none px-1">
                    <span class="text-[10px] font-mono font-bold text-white drop-shadow-sm truncate">
                      RECT
                    </span>
                    <span class="text-[9px] font-mono text-cyan-100 drop-shadow-sm truncate">
                      {{ ev.duration }}ns · a:{{ formatAmp(ev.event.amplitude) }}
                    </span>
                  </div>
                </div>

                <!-- 3. Custom Pulse -->
                <div
                  v-else-if="ev.kind === 'pulse'"
                  class="w-full h-full relative flex items-center justify-center rounded-lg overflow-hidden"
                  :class="selectedEvent?.id === ev.id ? 'ring-2 ring-sky-500' : ''"
                  :title="getEventTooltip(ev)"
                >
                  <svg viewBox="0 0 100 40" preserveAspectRatio="none" class="w-full h-full">
                    <defs>
                      <linearGradient :id="'custom-' + ev.id" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#0284c7" stop-opacity="0.8" />
                        <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.25" />
                      </linearGradient>
                    </defs>
                    <path d="M 0,38 C 15,38 25,6 35,6 L 65,6 C 75,6 85,38 100,38 Z" :fill="'url(#custom-' + ev.id + ')'" stroke="#0284c7" stroke-width="1.5" />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none px-1">
                    <span class="text-[10px] font-mono font-bold text-white drop-shadow-sm truncate">
                      CUSTOM
                    </span>
                    <span class="text-[9px] font-mono text-sky-100 drop-shadow-sm truncate">
                      {{ ev.duration }}ns · a:{{ formatAmp(ev.event.amplitude) }}
                    </span>
                  </div>
                </div>

                <!-- 4. Readout / Acquisition -->
                <div
                  v-else-if="ev.kind === 'readout'"
                  class="w-full h-full relative flex items-center rounded-lg border border-dashed border-amber-300 bg-amber-50/70 overflow-hidden"
                  :class="selectedEvent?.id === ev.id ? 'ring-2 ring-amber-500' : ''"
                  :title="getEventTooltip(ev)"
                >
                  <!-- Probe pulse portion inside acquisition -->
                  <div
                    v-if="ev.event.probe?.duration"
                    class="h-full bg-amber-200/80 border-r border-amber-400 flex flex-col items-center justify-center px-1"
                    :style="{ width: `${(ev.event.probe.duration / ev.duration) * 100}%` }"
                  >
                    <span class="text-[9px] font-mono font-bold text-amber-900 truncate">
                      PROBE {{ ev.event.probe.duration }}ns
                    </span>
                    <span class="text-[8px] font-mono text-amber-700 truncate">
                      a:{{ formatAmp(ev.event.probe.amplitude) }}
                    </span>
                  </div>
                  <div class="flex-1 px-2 text-[10px] font-mono font-semibold text-amber-800 truncate">
                    ACQUISITION WINDOW ({{ ev.duration }} ns)
                  </div>
                </div>

                <!-- 5. Delay -->
                <div
                  v-else-if="ev.kind === 'delay'"
                  class="w-full h-full rounded-lg bg-gray-100/90 border border-dashed border-gray-300 flex items-center justify-center px-1"
                  :class="selectedEvent?.id === ev.id ? 'ring-2 ring-gray-400' : ''"
                  :title="`Delay: ${ev.duration} ns`"
                >
                  <span class="text-[10px] font-mono text-gray-500 truncate">
                    Delay {{ ev.duration }}ns
                  </span>
                </div>

                <!-- 6. Virtual Z (Instantaneous Phase) -->
                <div
                  v-else-if="ev.kind === 'virtualz'"
                  class="relative -translate-x-1/2 flex flex-col items-center z-10"
                  :title="`Virtual Z phase: ${ev.event.phase} rad`"
                >
                  <div class="w-0.5 h-12 bg-purple-600"></div>
                  <span class="px-1.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#833dff] text-white shadow-xs whitespace-nowrap">
                    Z({{ formatPhase(ev.event.phase) }})
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Event Details Inspector -->
    <div
      v-if="selectedEvent"
      class="px-4 py-3 bg-purple-50/40 border-t border-purple-100 flex flex-wrap items-center justify-between gap-3 text-xs"
    >
      <div class="flex items-center gap-3 flex-wrap min-w-0 font-mono">
        <span class="font-bold text-purple-900">
          Selected: {{ selectedEvent.channel }} ({{ selectedEvent.kind }})
        </span>
        <span v-if="selectedEvent.duration !== undefined" class="text-gray-600">
          Duration: <strong>{{ selectedEvent.duration }} ns</strong>
        </span>
        <span v-if="selectedEvent.event.amplitude !== undefined" class="text-gray-600">
          Amplitude: <strong>{{ selectedEvent.event.amplitude }}</strong>
        </span>
        <span v-if="selectedEvent.event.envelope?.kind" class="text-gray-600">
          Envelope: <strong>{{ selectedEvent.event.envelope.kind }}</strong>
        </span>
        <span v-if="selectedEvent.event.envelope?.beta !== undefined" class="text-gray-600">
          Beta: <strong>{{ selectedEvent.event.envelope.beta }}</strong>
        </span>
        <span v-if="selectedEvent.event.phase !== undefined" class="text-gray-600">
          Phase: <strong>{{ selectedEvent.event.phase }} rad</strong>
        </span>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="copyEventJson(selectedEvent)"
          class="px-2.5 py-1 rounded-lg bg-white hover:bg-purple-100 text-purple-800 border border-purple-200 text-xs font-semibold inline-flex items-center gap-1 transition cursor-pointer"
        >
          <span>Copy Event JSON</span>
        </button>
        <button
          type="button"
          @click="selectedEvent = null"
          class="text-gray-400 hover:text-gray-600 cursor-pointer font-bold px-1.5"
        >
          ✕
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { copyToClipboard } from '../../utils/clipboard.js'

const props = defineProps({
  sequence: {
    type: Array,
    required: true
  },
  gateName: {
    type: String,
    default: 'Native Gate'
  }
})

const selectedEvent = ref(null)
const copyStatusText = ref('Copy JSON')

function selectEvent(ev) {
  selectedEvent.value = ev
}

const parsedTimeline = computed(() => {
  const channelMap = new Map()

  // Initialize channels
  props.sequence.forEach(([ch]) => {
    if (!channelMap.has(ch)) {
      channelMap.set(ch, {
        channel: ch,
        events: [],
        currentTime: 0,
        totalDuration: 0
      })
    }
  })

  // Populate events
  props.sequence.forEach(([ch, event], idx) => {
    const track = channelMap.get(ch)
    if (!track) return

    const startTime = track.currentTime
    let duration = 0

    if (event.kind === 'readout') {
      const acqDur = event.acquisition?.duration || 0
      const probeDur = event.probe?.duration || 0
      duration = Math.max(acqDur, probeDur)
    } else if (typeof event.duration === 'number') {
      duration = event.duration
    } else if (event.kind === 'virtualz') {
      duration = 0
    }

    const endTime = startTime + duration
    track.events.push({
      id: `${ch}-${idx}`,
      index: idx,
      channel: ch,
      startTime,
      duration,
      endTime,
      event,
      kind: event.kind
    })

    track.currentTime = endTime
    track.totalDuration = Math.max(track.totalDuration, endTime)
  })

  const tracks = Array.from(channelMap.values())
  const maxDur = Math.max(...tracks.map(t => t.totalDuration), 40)
  return { tracks, maxDuration: maxDur }
})

const channelTracks = computed(() => parsedTimeline.value.tracks)
const totalDuration = computed(() => parsedTimeline.value.maxDuration)

const timeTicks = computed(() => {
  const dur = totalDuration.value
  const step = dur <= 100 ? 20 : dur <= 500 ? 100 : 400
  const ticks = []
  for (let t = step; t < dur; t += step) {
    ticks.push(t)
  }
  return ticks
})

const tickPercents = computed(() => {
  const dur = totalDuration.value
  return timeTicks.value.map(t => (t / dur) * 100)
})

function getEventStyle(ev) {
  const total = totalDuration.value
  const left = (ev.startTime / total) * 100

  if (ev.kind === 'virtualz') {
    return {
      left: `${left}%`,
      width: '0px'
    }
  }

  const width = Math.max((ev.duration / total) * 100, 2)
  return {
    left: `${left}%`,
    width: `${width}%`
  }
}

function isSmoothEnvelope(ev) {
  const k = ev.event.envelope?.kind
  return k === 'drag' || k === 'gaussian'
}

function isRectangularEnvelope(ev) {
  const k = ev.event.envelope?.kind
  return k === 'rectangular' || !k
}

function getChannelTagClass(ch) {
  if (ch.includes('/drive')) return 'bg-purple-100 text-purple-800 border border-purple-200'
  if (ch.includes('/flux')) return 'bg-cyan-100 text-cyan-800 border border-cyan-200'
  if (ch.includes('/acquisition')) return 'bg-amber-100 text-amber-800 border border-amber-200'
  return 'bg-gray-100 text-gray-700 border border-gray-200'
}

function formatAmp(amp) {
  if (typeof amp !== 'number') return '0'
  return Number(amp.toFixed(3)).toString()
}

function formatPhase(phase) {
  if (typeof phase !== 'number') return '0'
  const deg = Math.round((phase * 180) / Math.PI)
  return `${deg}°`
}

function getEventTooltip(ev) {
  return `${ev.channel} [${ev.kind}]: ${ev.duration} ns, amp: ${ev.event.amplitude || 'N/A'}`
}

function copySequenceJson() {
  copyToClipboard(JSON.stringify(props.sequence, null, 2))
  copyStatusText.value = 'Copied!'
  setTimeout(() => {
    copyStatusText.value = 'Copy JSON'
  }, 1200)
}

function copyEventJson(ev) {
  copyToClipboard(JSON.stringify(ev.event, null, 2))
}
</script>

<style scoped>
.pulse-sequence-card {
  transform: translateZ(0);
}
</style>
