<script setup>
defineProps({
  label: String,
  value: [Number, String]
})
</script>

<template>
  <div class="card stat">
    <div>
      <div class="num">{{ value }}</div>
      <div class="lbl">{{ label }}</div>
    </div>
  </div>
</template>
