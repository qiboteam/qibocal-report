<template>
  <div class="my-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
    <div v-if="figure.title" class="text-sm font-semibold text-gray-800 mb-2 font-mono">
      {{ figure.title }}
    </div>
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
