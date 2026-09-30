<template>
  <div class="terminal-output">
    <div class="terminal-heading" :class="{ 'with-heading': $slots.heading }">
      <slot name="heading" />
      <div class="terminal-controls">
        <label class="terminal-follow"><input v-model="follow" type="checkbox" /> Follow output</label>
        <slot name="actions" />
      </div>
    </div>
    <pre ref="terminal" tabindex="0" :aria-label="label" @scroll="handleScroll"><code><span v-for="(segment, index) in segments" :key="index" :style="segment.style">{{ segment.text }}</span><span v-if="!text" class="terminal-placeholder">{{ placeholder }}</span></code></pre>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { ansiSegments } from '../../utils/ansi.js'

const props = defineProps({
  text: { type: String, default: '' },
  active: { type: Boolean, default: true },
  label: { type: String, default: 'Terminal output' },
  placeholder: { type: String, default: 'Waiting for output...' }
})
const terminal = ref(null)
const follow = ref(true)
const segments = computed(() => ansiSegments(props.text))

function handleScroll() {
  const element = terminal.value
  follow.value = element.scrollHeight - element.scrollTop - element.clientHeight < 24
}

watch([() => props.text, () => props.active, follow], async () => {
  await nextTick()
  if (props.active && follow.value && terminal.value) terminal.value.scrollTop = terminal.value.scrollHeight
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
