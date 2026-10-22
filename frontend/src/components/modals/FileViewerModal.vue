<!--
  A file over the page, where no tab can open it: inside the desktop
  application, or when a browser refuses the pop-up. Its text, to read, copy
  or download; Escape or a click outside closes it.
-->
<template>
  <div
    v-if="fileViewer.open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-[#f7f7f7]/80 backdrop-blur-sm"
    @pointerdown.self="closeFile"
    @keydown.esc="closeFile"
  >
    <div class="w-[min(48rem,calc(100vw-2.5rem))] max-h-[min(40rem,calc(100vh-4rem))] flex flex-col bg-white rounded-2xl shadow-xl p-5 text-xs" role="dialog" aria-modal="true" aria-labelledby="file-viewer-title">
      <div class="flex items-center gap-2 shrink-0">
        <h2 id="file-viewer-title" class="text-sm font-semibold text-gray-900 font-mono truncate">{{ fileViewer.name }}</h2>
        <button type="button" class="ml-auto shrink-0 px-2 py-1 rounded-lg text-gray-600 hover:text-[#833dff] hover:bg-purple-50 cursor-pointer" @click="copy">{{ copied ? 'Copied' : 'Copy' }}</button>
        <button type="button" class="shrink-0 px-2 py-1 rounded-lg text-gray-600 hover:text-[#833dff] hover:bg-purple-50 cursor-pointer" @click="download">Download</button>
        <button ref="closer" type="button" class="shrink-0 text-gray-400 hover:text-gray-700 cursor-pointer text-base leading-none px-1" title="Close" @click="closeFile">&times;</button>
      </div>
      <pre class="mt-3 min-h-0 overflow-auto overscroll-contain rounded-xl bg-gray-50 p-3 font-mono text-[11px] leading-relaxed text-gray-800 whitespace-pre">{{ fileViewer.text }}</pre>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { closeFile, fileViewer } from '../../utils/fileViewer.js'

const copied = ref(false)
const closer = ref(null)

// Focus on the dialog, so Escape closes it at once.
watch(() => fileViewer.open, open => {
  copied.value = false
  if (open) nextTick(() => closer.value?.focus())
})

async function copy() {
  try {
    await navigator.clipboard.writeText(fileViewer.text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1200)
  } catch {
    copied.value = false
  }
}

function download() {
  const url = URL.createObjectURL(new Blob([fileViewer.text], { type: 'text/plain' }))
  const link = document.createElement('a')
  link.href = url
  link.download = fileViewer.name || 'file.txt'
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
</script>
