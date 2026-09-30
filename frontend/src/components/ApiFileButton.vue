<template>
  <button
    type="button"
    class="disabled:opacity-50"
    :disabled="busy || !path"
    :aria-busy="busy"
    @click="handleClick"
  >
    <slot />
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { downloadApiFile, openApiFile } from '../utils/apiFiles.js'

const props = defineProps({
  path: { type: String, required: true },
  filename: { type: String, default: 'download.zip' },
  preview: { type: Boolean, default: false }
})

const busy = ref(false)

async function handleClick() {
  if (busy.value) return
  busy.value = true
  try {
    if (props.preview) {
      await openApiFile(props.path)
    } else {
      await downloadApiFile(props.path, props.filename)
    }
  } catch (err) {
    window.alert(`Failed to ${props.preview ? 'open' : 'download'} file: ${err.message}`)
  } finally {
    busy.value = false
  }
}
</script>
