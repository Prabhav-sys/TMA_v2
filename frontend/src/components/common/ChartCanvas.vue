<script setup>
import { Chart, registerables } from 'chart.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

Chart.register(...registerables)

const props = defineProps({
  type: { type: String, default: 'bar' },
  labels: Array,
  values: Array,
  label: { type: String, default: 'Count' }
})

const canvas = ref(null)
let chart = null

function draw() {
  if (chart) chart.destroy()
  const isRound = props.type === 'pie' || props.type === 'doughnut'

  chart = new Chart(canvas.value, {
    type: props.type,
    data: {
      labels: props.labels,
      datasets: [
        {
          label: props.label,
          data: props.values
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: isRound
        ? {}
        : {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 }
            }
          }
    }
  })
}

onMounted(draw)
watch(() => [props.labels, props.values], draw, { deep: true })
onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
</script>

<template>
  <div class="chart-box">
    <canvas ref="canvas"></canvas>
  </div>
</template>
