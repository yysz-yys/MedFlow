<template>
  <el-drawer
    :model-value="visible"
    direction="rtl"
    size="440px"
    @close="$emit('close')"
    :title="panelTitle"
  >
    <div class="panel-body">
      <div class="period-hint">{{ periods.morning.label }} ｜ {{ periods.afternoon.label }} ｜ {{ periods.evening.label }}</div>
      <!-- 预设时段 -->
      <div class="section-title">预设时段</div>
      <div v-for="slot in presetSlots" :key="slot.key" class="preset-row">
        <el-checkbox v-model="slot.checked" @change="onSlotToggle(slot)">
          {{ slot.label }}
        </el-checkbox>
        <div v-if="slot.checked" class="preset-detail">
          <el-time-picker
            :model-value="slot.start"
            @update:model-value="(v: string) => slot.start = v"
            format="HH:mm" value-format="HH:mm"
            size="small" style="width: 110px"
          />
          <span>-</span>
          <el-time-picker
            :model-value="slot.end"
            @update:model-value="(v: string) => slot.end = v"
            format="HH:mm" value-format="HH:mm"
            size="small" style="width: 110px"
          />
          <span class="preset-label">最大挂号</span>
          <el-input-number
            v-model="slot.maxPatients"
            :min="1" :max="999"
            size="small" style="width: 80px"
          />
        </div>
      </div>

      <!-- 自定义时段 -->
      <div class="section-title" style="margin-top: 20px">自定义时段</div>
      <div v-for="(cs, idx) in customSlots" :key="idx" class="slot-row">
        <el-time-picker
          v-model="cs.start"
          format="HH:mm"
          value-format="HH:mm"
          size="small"
          style="width: 110px"
          placeholder="开始"
        />
        <span>-</span>
        <el-time-picker
          v-model="cs.end"
          format="HH:mm"
          value-format="HH:mm"
          size="small"
          style="width: 110px"
          placeholder="结束"
        />
        <el-input-number
          v-model="cs.maxPatients"
          :min="1"
          :max="999"
          size="small"
          style="width: 80px"
          placeholder="人数"
        />
        <el-button
          :icon="Delete"
          circle
          size="small"
          type="danger"
          plain
          @click="customSlots.splice(idx, 1)"
        />
      </div>
      <el-button size="small" style="margin-top: 8px" @click="addCustomSlot">
        + 添加自定义时段
      </el-button>

      <!-- 删除操作 -->
      <div v-if="existingSchedules.length > 0" style="margin-top: 24px">
        <div class="section-title">已有排班</div>
        <div
          v-for="s in existingSchedules"
          :key="s.id"
          class="existing-row"
        >
          <span>{{ s.start_time.substring(0, 5) }} - {{ s.end_time.substring(0, 5) }} ({{ s.max_patients }}人)</span>
          <div class="existing-actions">
            <span class="status-label" :style="{ color: s.status === 1 ? '#67c23a' : '#f56c6c' }">
              {{ s.status === 1 ? '可预约' : '停诊' }}
            </span>
            <el-switch
              :model-value="s.status === 1"
              size="small"
              @change="(val: boolean) => handleToggleStatus(s, val)"
            />
            <el-button size="small" type="danger" plain @click="handleDelete(s.id)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { doctorSchedulesApi } from '@medflow/shared'
import type { DoctorSchedule, SchedulePeriods } from '@medflow/shared'

const props = defineProps<{
  visible: boolean
  doctorId: number | null
  doctorName: string
  date: string
  existingSchedules: DoctorSchedule[]
  batchCells?: Array<{ doctorId: number; date: string }>
  periods: SchedulePeriods
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const saving = ref(false)

interface SlotItem {
  key: string
  label: string
  checked: boolean
  start: string
  end: string
  maxPatients: number
}

const presetSlots = reactive<SlotItem[]>([])

interface CustomSlot {
  start: string
  end: string
  maxPatients: number
}

const customSlots = reactive<CustomSlot[]>([])

const panelTitle = computed(() => {
  if (!props.date) return '排班编辑'
  const d = new Date(props.date)
  const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${props.doctorName} · ${dayNames[d.getDay()]} ${props.date}`
})

// 面板打开时重置
watch(() => props.visible, (v) => {
  if (v) {
    const p = props.periods
    presetSlots.splice(0, presetSlots.length,
      { key: 'morning',   label: '上午', checked: false, start: p.morning.start,   end: p.morning.end,   maxPatients: 20 },
      { key: 'afternoon', label: '下午', checked: false, start: p.afternoon.start, end: p.afternoon.end, maxPatients: 20 },
      { key: 'evening',   label: '晚上', checked: false, start: p.evening.start,   end: p.evening.end,   maxPatients: 15 },
    )
    customSlots.splice(0, customSlots.length)
  }
})

function onSlotToggle(slot: SlotItem) {
  const p = props.periods
  if (slot.key === 'morning') { slot.start = p.morning.start; slot.end = p.morning.end }
  else if (slot.key === 'afternoon') { slot.start = p.afternoon.start; slot.end = p.afternoon.end }
  else if (slot.key === 'evening') { slot.start = p.evening.start; slot.end = p.evening.end }
}

function addCustomSlot() {
  customSlots.push({ start: '', end: '', maxPatients: 20 })
}

async function handleToggleStatus(schedule: DoctorSchedule, active: boolean) {
  try {
    await doctorSchedulesApi.updateSchedule(schedule.id, { status: active ? 1 : 0 })
    schedule.status = active ? 1 : 0
    ElMessage.success(active ? '已设为可预约' : '已设为停诊')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleDelete(scheduleId: number) {
  try {
    await ElMessageBox.confirm('确定要删除该排班吗？')
    await doctorSchedulesApi.deleteSchedule(scheduleId)
    ElMessage.success('已删除')
    emit('saved')
  } catch { /* 取消 */ }
}

async function handleSave() {
  if (!props.doctorId) { ElMessage.warning('未选择医生'); return }
  saving.value = true
  try {
    const toCreate: Array<{ start: string; end: string; maxPatients: number }> = []

    for (const s of presetSlots) {
      if (s.checked && s.start && s.end) {
        toCreate.push({ start: s.start, end: s.end, maxPatients: s.maxPatients })
      }
    }
    for (const cs of customSlots) {
      if (cs.start && cs.end) {
        toCreate.push({ start: cs.start, end: cs.end, maxPatients: cs.maxPatients })
      }
    }

    for (const item of toCreate) {
      await doctorSchedulesApi.createSchedule({
        doctor_id: props.doctorId,
        work_date: props.date,
        start_time: item.start,
        end_time: item.end,
        max_patients: item.maxPatients,
      })
    }

    ElMessage.success('保存成功')
    emit('saved')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.panel-body {
  padding: 0 4px;
}
.period-hint { font-size: 12px; color: #409eff; background: #ecf5ff; padding: 6px 10px; border-radius: 4px; margin-bottom: 12px; }
.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}
.slot-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.preset-row {
  margin-bottom: 8px;
}
.preset-detail {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.preset-label {
  font-size: 13px;
  color: #606266;
}
.slot-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.existing-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}
.existing-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-label {
  font-size: 13px;
  font-weight: 500;
  min-width: 42px;
  text-align: right;
}
</style>
