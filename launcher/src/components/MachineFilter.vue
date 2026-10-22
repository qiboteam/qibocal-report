<!--
  Filter a list by the machine its entries reach: chips while they are few,
  a dropdown past that. Shown only when there is a choice to make.
-->
<template>
  <div v-if="options.length > 2" class="flex flex-wrap items-center gap-1.5">
    <span class="text-[11px] text-gray-400 shrink-0">Machine</span>
    <select v-if="options.length > 6" :value="modelValue" class="lx-select !py-0.5 text-xs" aria-label="Machine" @change="$emit('update:modelValue', $event.target.value)">
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
    <template v-else>
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="lx-chip"
        :class="{ 'is-on': modelValue === option.value }"
        @click="$emit('update:modelValue', option.value)"
      >{{ option.label }}</button>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { machines } from '../state.js'
import { machineOptions } from '../lib/machines.js'

const props = defineProps({
  /** The destinations the list's entries reach; empty for this machine. */
  destinations: { type: Array, default: () => [] },
  /** `all`, `local`, or a machine's label. */
  modelValue: { type: String, default: 'all' }
})
defineEmits(['update:modelValue'])

const options = computed(() => machineOptions(props.destinations, machines.value))
</script>
