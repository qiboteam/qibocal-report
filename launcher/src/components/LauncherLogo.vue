<!--
  The launcher mark: an orbit around a play triangle.

  Two ideas in one glyph — the orbital ring of the quantum subject, and the
  core that starts something — and no text, so the same drawing works in the
  page corner, over the dashboard and, filled in white on its purple plate, as
  the application icon in `src-tauri/icon.svg`.
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
    <ellipse
      cx="16"
      cy="16"
      rx="14"
      ry="6.4"
      transform="rotate(-28 16 16)"
      stroke="currentColor"
      :stroke-width="stroke"
      opacity="0.9"
    />
    <path
      d="M13.4 11.5 L21.2 16 L13.4 20.5 Z"
      fill="currentColor"
      stroke="currentColor"
      :stroke-width="stroke"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 26 },
  /** Thicker strokes survive the small sizes; thinner ones suit a large mark. */
  stroke: { type: [Number, String], default: 2.2 }
})
</script>
