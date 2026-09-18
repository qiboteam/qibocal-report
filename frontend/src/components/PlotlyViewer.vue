<template>
  <div class="my-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm relative">
    <div v-if="figure.title" class="text-sm font-semibold text-gray-800 mb-2 font-mono pr-48">
      {{ figure.title }}
    </div>
    <div v-else class="h-3"></div>
    <div ref="plotContainer" class="w-full min-h-[350px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, toRaw } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  figure: { type: Object, required: true }
})

const plotContainer = ref(null)
let isRendered = false

function getCleanDataAndLayout() {
  const fig = toRaw(props.figure)
  const rawData = fig.data ? JSON.parse(JSON.stringify(fig.data)) : []
  const rawLayout = {
    autosize: true,
    font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { t: 30, r: 20, b: 40, l: 50 },
    hovermode: 'closest',
    modebar: {
      orientation: 'h',
      bgcolor: 'transparent',
      color: '#6b7280',
      activecolor: '#833dff',
      ...(fig.layout?.modebar || {})
    },
    ...(fig.layout ? JSON.parse(JSON.stringify(fig.layout)) : {})
  }
  return { rawData, rawLayout }
}

async function renderPlot() {
  await nextTick()
  if (!plotContainer.value || !props.figure) return

  const { rawData, rawLayout } = getCleanDataAndLayout()

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  }

  try {
    // Plotly.react is high-performance and reuses the graph div safely
    await Plotly.react(plotContainer.value, rawData, rawLayout, config)
    isRendered = true
  } catch (err) {
    console.error('Error rendering Plotly figure:', err)
  }
}

let resizeTimer = null
function handleResize() {
  if (resizeTimer) cancelAnimationFrame(resizeTimer)
  resizeTimer = requestAnimationFrame(() => {
    if (plotContainer.value && isRendered) {
      Plotly.Plots.resize(plotContainer.value)
    }
  })
}

onMounted(() => {
  requestAnimationFrame(() => {
    renderPlot()
  })
  window.addEventListener('resize', handleResize)
  window.addEventListener('beforeprint', handleResize)
  window.addEventListener('afterprint', handleResize)
})

// Shallow watch on figure identity/title only - NEVER deep watch mutable Plotly figures!
watch(() => [props.figure?.id, props.figure?.title], () => {
  renderPlot()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('beforeprint', handleResize)
  window.removeEventListener('afterprint', handleResize)
  if (resizeTimer) cancelAnimationFrame(resizeTimer)
  if (plotContainer.value) {
    Plotly.purge(plotContainer.value)
  }
})
</script>

<style scoped>
/* Plotly Modebar Styling - Injected in container to match web app UI */
:deep(.modebar-container) {
  top: -26px !important;
  right: 4px !important;
  z-index: 20 !important;
  transition: opacity 0.2s ease-in-out;
}

:deep(.modebar-container:hover .modebar) {
  opacity: 1 !important;
}

:deep(.modebar) {
  background: rgba(255, 255, 255, 0.96) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  padding: 2px 4px !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 2px !important;
}

:deep(.modebar-group) {
  display: inline-flex !important;
  align-items: center !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
}

:deep(.modebar-group:not(:last-child)) {
  border-right: 1px solid #f3f4f6 !important;
  padding-right: 3px !important;
  margin-right: 3px !important;
}

:deep(.modebar-btn) {
  height: 24px !important;
  width: 24px !important;
  padding: 3px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 0.375rem !important;
  cursor: pointer !important;
  transition: background-color 0.15s ease, color 0.15s ease !important;
  margin: 0 !important;
}

:deep(.modebar-btn:hover) {
  background-color: #f3f0ff !important;
}

:deep(.modebar-btn.active) {
  background-color: #ebe0ff !important;
}

:deep(.modebar-btn svg) {
  height: 14px !important;
  width: 14px !important;
  position: static !important;
  top: auto !important;
}

:deep(.modebar-btn svg path) {
  fill: #6b7280 !important;
  transition: fill 0.15s ease !important;
}

:deep(.modebar-btn:hover svg path) {
  fill: #833dff !important;
}

:deep(.modebar-btn.active svg path) {
  fill: #833dff !important;
}

/* Tooltip on hover */
:deep([data-title]:hover:after) {
  background-color: #111827 !important;
  color: #f9fafb !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  font-size: 11px !important;
  font-weight: 500 !important;
  border-radius: 0.375rem !important;
  padding: 4px 8px !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep([data-title]:hover:before) {
  border-bottom-color: #111827 !important;
}
</style>
