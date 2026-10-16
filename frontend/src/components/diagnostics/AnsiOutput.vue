<template>
  <div class="terminal-output">
    <div class="terminal-heading" :class="{ 'with-heading': $slots.heading }">
      <slot name="heading" />
      <div class="terminal-controls">
        <label class="terminal-follow"><input v-model="follow" type="checkbox" /> Follow output</label>
        <slot name="actions" />
      </div>
    </div>
    <pre ref="terminal" tabindex="0" :aria-label="label" :style="maxHeight ? { maxHeight } : undefined" @scroll="handleScroll"><code><span v-for="(segment, index) in segments" :key="index" :style="segment.style">{{ segment.text }}</span><span v-if="!text" class="terminal-placeholder">{{ placeholder }}</span></code></pre>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { ansiSegments } from '../../utils/ansi.js'

const props = defineProps({
  text: { type: String, default: '' },
  active: { type: Boolean, default: true },
  label: { type: String, default: 'Terminal output' },
  placeholder: { type: String, default: 'Waiting for output...' },
  /**
   * A ceiling for the output, as CSS — `55vh`, say. Within it the output
   * scrolls by itself, and "Follow output" has something to follow: left
   * unset, the output grows with its content and the page scrolls instead.
   */
  maxHeight: { type: String, default: '' }
})
const terminal = ref(null)
const follow = ref(true)
const segments = computed(() => ansiSegments(props.text))

/** How close to the bottom counts as "at the bottom": a couple of lines. */
const THRESHOLD = 40
let scrollingProgrammatically = false

/**
 * Following tracks the reader: scrolled up, it stops, so new output does
 * not pull the view away from what is being read; scrolled back down to
 * within the threshold, it resumes. Our own scrolls to the bottom do not
 * count as the reader's.
 */
function handleScroll() {
  if (scrollingProgrammatically) return
  const element = terminal.value
  if (!element) return
  follow.value = element.scrollHeight - element.scrollTop - element.clientHeight < THRESHOLD
}

function scrollToBottom() {
  const element = terminal.value
  if (!element) return
  scrollingProgrammatically = true
  element.scrollTop = element.scrollHeight
  requestAnimationFrame(() => { scrollingProgrammatically = false })
}

// New output, or following switched on, brings the bottom into view.
watch([() => props.text, () => props.active, follow], async () => {
  await nextTick()
  if (follow.value) scrollToBottom()
})
</script>

<style scoped>
.terminal-output { display: flex; flex-direction: column; min-height: 0; flex: 1; }
.terminal-heading { display: flex; align-items: center; gap: 12px; padding: 6px 12px; }
.terminal-controls { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.with-heading .terminal-controls { margin-left: auto; }
.terminal-follow { font-size: 11px; color: #aaa; white-space: nowrap; }
pre { flex: 1; min-height: 80px; margin: 0; padding: 10px 14px; overflow: auto; background: #1e1e1e; color: #d4d4d4; font: 12px/1.6 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; tab-size: 4; white-space: pre-wrap; overflow-wrap: anywhere; }
.terminal-placeholder { color: #aaa; }
</style>
