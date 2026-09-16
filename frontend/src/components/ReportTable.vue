<template>
  <div class="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
    <table class="w-full text-left border-collapse text-sm">
      <thead>
        <tr class="bg-gray-50/80 border-b border-gray-100 text-xs text-gray-500 uppercase font-semibold">
          <th class="py-3 px-4">Title / ID</th>
          <th class="py-3 px-4">Platform</th>
          <th class="py-3 px-4">Qubits</th>
          <th class="py-3 px-4">Protocols</th>
          <th class="py-3 px-4">Author</th>
          <th class="py-3 px-4">Date</th>
          <th class="py-3 px-4 text-right">Action</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr 
          v-for="report in reports" 
          :key="report.id"
          @click="$emit('select', report)"
          class="hover:bg-purple-50/30 cursor-pointer transition"
        >
          <td class="py-3.5 px-4">
            <div class="font-semibold text-gray-900 hover:text-[#833dff]">{{ report.title }}</div>
            <div class="text-xs font-mono text-gray-400 truncate max-w-xs">{{ report.id }}</div>
          </td>
          <td class="py-3.5 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              {{ report.platform }}
            </span>
          </td>
          <td class="py-3.5 px-4 font-mono text-xs text-gray-600">
            Q{{ report.targets.join(', Q') }}
          </td>
          <td class="py-3.5 px-4">
            <div class="flex flex-wrap gap-1 max-w-sm">
              <span 
                v-for="proto in report.protocols.slice(0, 3)" 
                :key="proto"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700"
              >
                {{ proto.replace('_', ' ') }}
              </span>
              <span 
                v-if="report.protocols.length > 3" 
                class="text-[11px] text-gray-400 font-medium px-1"
              >
                +{{ report.protocols.length - 3 }}
              </span>
            </div>
          </td>
          <td class="py-3.5 px-4 text-gray-600 text-xs">
            {{ report.author }}
          </td>
          <td class="py-3.5 px-4 text-gray-500 text-xs whitespace-nowrap">
            <div>{{ report.date }}</div>
            <div class="text-[10px] text-gray-400">{{ report.time }}</div>
          </td>
          <td class="py-3.5 px-4 text-right">
            <button 
              @click.stop="$emit('select', report)"
              class="px-3 py-1.5 text-xs font-semibold rounded-lg bm-btn-secondary"
            >
              View
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  reports: { type: Array, required: true }
})

defineEmits(['select'])
</script>
