<template>
  <div class="week-toolbar">
    <div class="week-nav">
      <el-button :icon="ArrowLeft" circle size="small" @click="prevWeek" />
      <span class="week-label">
        {{ weekLabel }}
      </span>
      <el-button :icon="ArrowRight" circle size="small" @click="nextWeek" />
      <el-button size="small" @click="goToday">今天</el-button>
    </div>
    <div class="week-actions">
      <span class="period-hint">{{ periods.hintShort }}</span>
      <el-dropdown @command="(type: string) => $emit('fillAll', type as any)">
        <el-button size="small">
          全部排满 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="morning">全部排满上午</el-dropdown-item>
            <el-dropdown-item command="afternoon">全部排满下午</el-dropdown-item>
            <el-dropdown-item command="full">全部排满全天</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button size="small" @click="$emit('editDefaultTemplate')">默认模板设置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import { getWeekRange, formatDate } from '@/utils/week'
import type { SchedulePeriods } from '@medflow/shared'

const props = defineProps<{
  weekStart: Date
  periods: SchedulePeriods
}>()
const emit = defineEmits<{
  'update:weekStart': [d: Date]
  fillAll: [type: 'morning' | 'afternoon' | 'full']
  editDefaultTemplate: []
}>()

const weekLabel = computed(() => {
  const { start, end } = getWeekRange(props.weekStart)
  return `${formatDate(start)} - ${formatDate(end)}`
})

function prevWeek() {
  const d = new Date(props.weekStart)
  d.setDate(d.getDate() - 7)
  emit('update:weekStart', d)
}
function nextWeek() {
  const d = new Date(props.weekStart)
  d.setDate(d.getDate() + 7)
  emit('update:weekStart', d)
}
function goToday() {
  const now = new Date()
  const { start } = getWeekRange(now)
  emit('update:weekStart', start)
}
</script>

<style scoped>
.week-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 12px;
}
.week-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}
.week-label {
  font-size: 15px;
  font-weight: 500;
  min-width: 220px;
  text-align: center;
}
.week-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.period-hint {
  font-size: 12px;
  color: #409eff;
  white-space: nowrap;
  flex-shrink: 0;
}
</style>
