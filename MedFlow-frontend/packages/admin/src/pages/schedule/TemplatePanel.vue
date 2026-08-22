<template>
  <el-drawer
    :model-value="visible"
    direction="rtl"
    size="520px"
    @close="$emit('close')"
    :title="isDefault ? '全院默认排班模板' : `${doctorName} · 专属排班模板`"
  >
    <div class="template-body">
      <p class="template-hint" v-if="!isDefault">
        未设置的时段将走默认模板。如需清除专属模板恢复默认，点下方按钮。
      </p>

      <table class="template-grid">
        <thead>
          <tr>
            <th class="tg-label"></th>
            <th v-for="d in DAYS" :key="d.i" class="tg-day">{{ d.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="slot in slots" :key="slot.key">
            <td class="tg-label">{{ slot.label }}<br><span class="tg-time">{{ slot.timeRange }}</span></td>
            <td
              v-for="d in DAYS" :key="d.i"
              class="tg-cell"
              :class="{ checked: isChecked(slot.key, d.i) }"
              @click="toggle(slot.key, d.i)"
            >
              {{ isChecked(slot.key, d.i) ? '✓' : '' }}
            </td>
          </tr>
        </tbody>
      </table>

      <div style="margin-top: 16px">
        <span style="font-size: 13px; color: #606266">最大挂号数: </span>
        <el-input-number v-model="maxPatients" :min="1" :max="999" size="small" style="width: 100px" />
      </div>

      <div style="margin-top: 24px">
        <el-button v-if="isDefault" size="small" @click="resetToDefault">重置为周一至周五全天</el-button>
        <el-button v-else type="danger" plain size="small" @click="handleClear">
          清除专属模板，使用默认模板
        </el-button>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button :loading="saving" @click="handleSave('next')">下周生效</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave('now')">立即生效</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { doctorSchedulesApi } from '@medflow/shared'
import type { TemplateSlot, SchedulePeriods } from '@medflow/shared'

const DAYS = [
  { i: 0, label: '周日' }, { i: 1, label: '周一' }, { i: 2, label: '周二' },
  { i: 3, label: '周三' }, { i: 4, label: '周四' }, { i: 5, label: '周五' }, { i: 6, label: '周六' },
]

interface SlotDef { key: string; label: string; timeRange: string }

const props = defineProps<{
  visible: boolean
  doctorId: number | null
  doctorName: string
  isDefault: boolean
  periods: SchedulePeriods
}>()

const slots = computed<SlotDef[]>(() => [
  { key: 'morning',   label: '上午', timeRange: `${props.periods.morning.start}-${props.periods.morning.end}` },
  { key: 'afternoon', label: '下午', timeRange: `${props.periods.afternoon.start}-${props.periods.afternoon.end}` },
  { key: 'evening',   label: '晚上', timeRange: `${props.periods.evening.start}-${props.periods.evening.end}` },
])

const emit = defineEmits<{
  close: []
  saved: [action: 'now' | 'next']
}>()

const saving = ref(false)
const maxPatients = ref(20)
const checked = reactive<Record<string, boolean>>({})

function key(slotKey: string, weekday: number) { return `${slotKey}_${weekday}` }
function isChecked(slotKey: string, weekday: number) { return !!checked[key(slotKey, weekday)] }
function toggle(slotKey: string, weekday: number) {
  const k = key(slotKey, weekday)
  checked[k] = !checked[k]
}

function resetToDefault() {
  for (const k of Object.keys(checked)) delete checked[k]
  maxPatients.value = 20
  for (const slot of slots.value) {
    for (let wd = 1; wd <= 5; wd++) checked[key(slot.key, wd)] = true
  }
}

watch(() => props.visible, async (v) => {
  if (!v) return
  for (const k of Object.keys(checked)) delete checked[k]
  maxPatients.value = 20
  if (props.isDefault || !props.doctorId) {
    const hasData = await loadExisting(0)
    if (!hasData) resetToDefault()
  } else {
    // 先加载专属模板，无数据则加载默认模板作为展示
    const hasData = await loadExisting(-props.doctorId)
    if (!hasData) await loadExisting(0)
  }
})

async function loadExisting(templateDoctorId: number): Promise<boolean> {
  try {
    const res = await doctorSchedulesApi.listTemplates(templateDoctorId)
    if (res.data.length === 0) return false
    for (const item of res.data) {
      if (item.id === 0 && item.doctor_id === 0) continue // 兜底虚拟记录
      const d = new Date(item.work_date + 'T00:00:00')
      const weekday = d.getDay() // 0=Sun
      const start = item.start_time.substring(0, 5)
      const p = props.periods
      let slotKey = ''
      if (start === p.morning.start) slotKey = 'morning'
      else if (start === p.afternoon.start) slotKey = 'afternoon'
      else if (start === p.evening.start) slotKey = 'evening'
      if (slotKey) checked[key(slotKey, weekday)] = true
      if (item.max_patients) maxPatients.value = item.max_patients
    }
    return true
  } catch { return false }
}

async function handleSave(action: 'now' | 'next') {
  saving.value = true
  try {
    const templateDoctorId = props.isDefault ? 0 : -(props.doctorId!)
    const p = props.periods
    const items: TemplateSlot[] = []
    for (const slot of slots.value) {
      for (const d of DAYS) {
        if (isChecked(slot.key, d.i)) {
          let start: string, end: string
          if (slot.key === 'morning') { start = p.morning.start; end = p.morning.end }
          else if (slot.key === 'afternoon') { start = p.afternoon.start; end = p.afternoon.end }
          else { start = p.evening.start; end = p.evening.end }
          items.push({ weekday: d.i, start_time: start, end_time: end, max_patients: maxPatients.value })
        }
      }
    }
    await doctorSchedulesApi.saveTemplate({ doctor_id: templateDoctorId, items })
    ElMessage.success('模板已保存')
    emit('saved', action)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function handleClear() {
  if (!props.doctorId) return
  try {
    await ElMessageBox.confirm(
      '确定清除该医生的专属模板吗？之后将走默认模板。',
      '清除专属模板',
      { confirmButtonText: '立即生效', cancelButtonText: '下周生效', distinguishCancelAndClose: true }
    )
    try {
      await doctorSchedulesApi.deleteTemplate(-props.doctorId)
      ElMessage.success('已清除专属模板')
      emit('saved', 'now')
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '清除模板失败')
    }
  } catch (action: any) {
    if (action === 'cancel') {
      try {
        await doctorSchedulesApi.deleteTemplate(-props.doctorId)
        ElMessage.success('已清除专属模板')
        emit('saved', 'next')
      } catch (e: any) {
        ElMessage.error(e.response?.data?.detail || '清除模板失败')
      }
    }
    // action === 'close': 用户点 X 关闭，忽略
  }
}
</script>

<style scoped>
.template-body { padding: 0 8px; }
.template-hint { font-size: 13px; color: #909399; margin-bottom: 16px; }
.template-grid { width: 100%; border-collapse: collapse; }
.template-grid th, .template-grid td { border: 1px solid #dcdfe6; padding: 8px 4px; text-align: center; font-size: 13px; }
.template-grid th { background: #f5f7fa; font-weight: 500; }
.tg-label { width: 80px; line-height: 1.4; }
.tg-time { font-size: 11px; color: #909399; }
.tg-day { width: calc((100% - 80px) / 7); }
.tg-cell { cursor: pointer; transition: background .15s; height: 36px; user-select: none; }
.tg-cell:hover { background: #ecf5ff; }
.tg-cell.checked { background: #67c23a; color: #fff; font-weight: bold; }
</style>
