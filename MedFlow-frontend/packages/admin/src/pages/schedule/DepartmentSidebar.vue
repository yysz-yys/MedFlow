<template>
  <div class="dept-sidebar">
    <el-input
      :model-value="searchKeyword"
      placeholder="搜索科室"
      clearable
      @input="$emit('update:searchKeyword', $event)"
      style="margin-bottom: 12px"
    />
    <div class="dept-list">
      <div
        v-for="dept in filteredDepartments"
        :key="dept.id"
        :class="['dept-item', { active: dept.id === selectedDeptId }]"
        @click="$emit('update:selectedDeptId', dept.id)"
      >
        <span class="dept-name">{{ dept.name }}</span>
        <span class="dept-count">{{ doctorCountMap[dept.id] ?? 0 }}人</span>
      </div>
      <div v-if="filteredDepartments.length === 0" class="dept-empty">
        无匹配科室
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Department } from '@medflow/shared'

const props = defineProps<{
  departments: Department[]
  selectedDeptId: number | null
  searchKeyword: string
  doctorCountMap: Record<number, number>
}>()

defineEmits<{
  'update:selectedDeptId': [id: number]
  'update:searchKeyword': [keyword: string]
}>()

const filteredDepartments = computed(() => {
  if (!props.searchKeyword) return props.departments
  const kw = props.searchKeyword.toLowerCase()
  return props.departments.filter(d => d.name.toLowerCase().includes(kw))
})
</script>

<style scoped>
.dept-sidebar {
  width: 180px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
  padding-right: 12px;
}
.dept-list {
  flex: 1;
  overflow-y: auto;
}
.dept-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  color: #303133;
}
.dept-item:hover {
  background: #f5f7fa;
}
.dept-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}
.dept-count {
  font-size: 12px;
  color: #909399;
}
.dept-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 20px 0;
  font-size: 13px;
}
</style>
