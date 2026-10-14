<!--
  The launcher mark: the Qibo Q, read as a dial.

  Three things make the Qibo logo recognisable — the bold ring, the bowl
  filling the lower half of its counter, and the tail that sweeps out as a
  swoosh — and all three are here, without the letters that follow. What
  Qibocal adds is calibration: three ticks over the ring, the scale of a
  gauge, so the Q is also a dial being read. No text, so the same drawing
  works in the page corner, over the dashboard and, in white on its purple
  plate, as the application icon in `src-tauri/icon.svg`.
-->
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 32 32"
    fill="none"
    role="img"
    aria-hidden="true"
    focusable="false"
  >
    <circle cx="14.5" cy="15.5" r="9.3" stroke="currentColor" stroke-width="3.2" />
    <path d="M 7 15.5 Q 12 8 20.8 20 A 7.7 7.7 0 0 1 7 15.5 Z" fill="currentColor" />
    <path d="M 20.2 20.6 C 23.6 25 27.4 26.6 31.2 27.1 C 26.2 27.6 22.4 26.4 19.1 23.4 Z" fill="currentColor" />
    <g stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <path d="M 8.2 4.6 L 7.1 2.7" />
      <path d="M 14.5 3 L 14.5 0.9" />
      <path d="M 20.8 4.6 L 21.9 2.7" />
    </g>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 26 }
})
</script>
