<template>
  <div class="my-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
    <div v-if="figure.title" class="text-sm font-semibold text-gray-800 mb-2 font-mono">
      {{ figure.title }}
    </div>
    <div ref="plotContainer" class="w-full min-h-[350px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  figure: { type: Object, required: true }
})

const plotContainer = ref(null)

async function renderPlot() {
  await nextTick()
  if (!plotContainer.value || !props.figure) return

  const layout = {
    autosize: true,
    font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { t: 30, r: 20, b: 40, l: 50 },
    hovermode: 'closest',
    ...(props.figure.layout || {})
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  }

  try {
    Plotly.newPlot(plotContainer.value, props.figure.data || [], layout, config)
  } catch (err) {
    console.error('Error rendering Plotly figure:', err)
  }
}

function handleResize() {
  if (plotContainer.value) {
    Plotly.Plots.resize(plotContainer.value)
  }
}

onMounted(() => {
  renderPlot()
  window.addEventListener('resize', handleResize)
})

watch(() => props.figure, () => {
  renderPlot()
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (plotContainer.value) {
    Plotly.purge(plotContainer.value)
  }
})
</script>
