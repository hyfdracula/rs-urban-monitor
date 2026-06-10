<template>
  <el-tag type="warning" size="small" effect="plain" class="mock-badge">
    {{ label }}
  </el-tag>
</template>

<script setup>
defineProps({
  label: { type: String, default: '估算数据' },
})
</script>

<style scoped>
.mock-badge {
  margin-left: 6px;
  font-size: 10px;
  line-height: 1;
  padding: 1px 4px;
  border-radius: 3px;
}
</style>
