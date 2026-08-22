<template>
  <div class="page" style="display:flex;gap:16px;height:100%">
    <DepartmentSidebar
      :departments="departments"
      :selectedDeptId="selectedDeptId"
      :searchKeyword="deptSearch"
      :doctorCountMap="doctorCountMap"
      @update:selectedDeptId="selectDept"
      @update:searchKeyword="deptSearch = $event"
    />

    <div v-if="selectedDeptId" style="flex:1;display:flex;flex-direction:column;min-width:0">
      <WeekToolbar
        :weekStart="weekStart"
        :periods="schedulePeriods"
        @update:weekStart="weekStart = $event"
        @fillAll="fillAll"
        @editDefaultTemplate="openDefaultTemplate"
      />

      <div style="flex:1;overflow:hidden;margin-top:12px" v-loading="loading">
        <ScheduleGrid
          :doctors="deptDoctors"
          :weekDates="weekDates"
          :schedules="schedules"
          :selectedCells="selectedCells"
          :doctorTemplates="doctorTemplates"
          :periods="schedulePeriods"
          @cellClick="onCellClick"
          @cellMouseDown="onCellMouseDown"
          @cellMouseEnter="onCellMouseEnter"
          @cellMouseUp="onCellMouseUp"
          @templateClick="openDoctorTemplate"
        />
      </div>

      <SchedulePanel
        :visible="panelVisible"
        :doctorId="editingDoctorId"
        :doctorName="editingDoctorName"
        :date="editingDate"
        :existingSchedules="editingSchedules"
        :batchCells="selectedCells"
        :periods="schedulePeriods"
        @close="panelVisible = false"
        @saved="onSaved"
      />

      <TemplatePanel
        :visible="templatePanelVisible"
        :doctorId="templateDoctorId"
        :doctorName="templateDoctorName"
        :isDefault="templateIsDefault"
        :periods="schedulePeriods"
        @close="templatePanelVisible = false"
        @saved="onTemplateSaved"
      />
    </div>

    <div v-else style="flex:1;display:flex;align-items:center;justify-content:center;color:#c0c4cc;font-size:14px">
      请从左侧选择一个科室
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { departmentsApi, doctorsApi, doctorSchedulesApi, systemConfigApi, parseScheduleConfig, type SchedulePeriods } from '@medflow/shared'
import type { Department, Doctor, DoctorSchedule } from '@medflow/shared'
import { getWeekDates, getWeekRange } from '@/utils/week'
import DepartmentSidebar from './schedule/DepartmentSidebar.vue'
import WeekToolbar from './schedule/WeekToolbar.vue'
import ScheduleGrid from './schedule/ScheduleGrid.vue'
import SchedulePanel from './schedule/SchedulePanel.vue'
import TemplatePanel from './schedule/TemplatePanel.vue'

// ========== 基础数据 ==========
const departments = ref<Department[]>([])
const allDoctors = ref<Doctor[]>([])
const schedules = ref<DoctorSchedule[]>([])
const schedulePeriods = ref<SchedulePeriods>(parseScheduleConfig())
const loading = ref(false)

// ========== 选择状态 ==========
const selectedDeptId = ref<number | null>(null)
const deptSearch = ref('')
const weekStart = ref(getWeekRange(new Date()).start)

// ========== 面板状态 ==========
const panelVisible = ref(false)
const editingDoctorId = ref<number | null>(null)
const editingDoctorName = ref('')
const editingDate = ref('')

// ========== 模板面板状态 ==========
const templatePanelVisible = ref(false)
const templateDoctorId = ref<number | null>(null)
const templateDoctorName = ref('')
const templateIsDefault = ref(false)
const doctorTemplates = ref<Record<number, boolean>>({})

// ========== 拖选状态 ==========
const selectedCells = ref<Array<{ doctorId: number; date: string }>>([])
let isDragging = false
let dragStartDoctorId = 0
let dragStartDate = ''

// ========== 计算属性 ==========
const weekDates = computed(() => getWeekDates(weekStart.value))

/** 每个科室的医生数量 */
const doctorCountMap = computed(() => {
  const map: Record<number, number> = {}
  for (const d of allDoctors.value) {
    if (d.department_id) {
      map[d.department_id] = (map[d.department_id] ?? 0) + 1
    }
  }
  return map
})

/** 当前选中科室的医生列表 */
const deptDoctors = computed(() => {
  if (!selectedDeptId.value) return []
  return allDoctors.value.filter(d => d.department_id === selectedDeptId.value)
})

/** 当前编辑格子的已有排班 */
const editingSchedules = computed(() => {
  if (!editingDoctorId.value || !editingDate.value) return []
  return schedules.value.filter(
    s => s.doctor_id === editingDoctorId.value && s.work_date === editingDate.value
  )
})

// ========== 监听 ==========
// 切换科室或周次 → 重新加载排班
watch([selectedDeptId, weekStart], () => {
  fetchSchedules()
})

// 关闭面板时清除选中
watch(panelVisible, (v) => {
  if (!v) {
    selectedCells.value = []
    isDragging = false
  }
})

// ========== 方法 ==========
onMounted(async () => {
  loading.value = true
  try {
    const [deptRes, docRes, configRes] = await Promise.all([
      departmentsApi.listDepartments({ page_size: 999 }),
      doctorsApi.listDoctors({ page_size: 999 }),
      systemConfigApi.getByKey('default_doctor_schedule').catch(() => null),
    ])
    departments.value = deptRes.data.items.filter(d => !d.deleted_at)
    allDoctors.value = docRes.data.items.filter(d => !d.deleted_at)
    if (configRes) {
      schedulePeriods.value = parseScheduleConfig(configRes.data.config_value)
    }
    // 默认选中第一个科室
    if (departments.value.length > 0) {
      selectedDeptId.value = departments.value[0].id
    }
    await loadTemplateInfo()
  } catch (e: any) {
    ElMessage.error('加载科室和医生数据失败')
  } finally {
    loading.value = false
  }
  // 初始加载排班
  if (selectedDeptId.value) {
    await fetchSchedules()
  }
})

async function fetchSchedules() {
  if (!selectedDeptId.value) return
  loading.value = true
  const { start, end } = getWeekRange(weekStart.value)
  const d1 = formatDateStr(start)
  const d2 = formatDateStr(end)
  try {
    const res = await doctorSchedulesApi.listSchedules({
      department_id: selectedDeptId.value,
      work_date_from: d1,
      work_date_to: d2,
    })
    schedules.value = res.data
  } catch (e: any) {
    ElMessage.error('加载排班失败')
  } finally {
    loading.value = false
  }
}

function formatDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function selectDept(id: number) {
  selectedDeptId.value = id
}

// ========== 模板管理 ==========
async function loadTemplateInfo() {
  const map: Record<number, boolean> = {}
  for (const doc of allDoctors.value) {
    try {
      const res = await doctorSchedulesApi.listTemplates(-doc.id)
      map[doc.id] = res.data.length > 0
    } catch { map[doc.id] = false }
  }
  doctorTemplates.value = map
}

function openDoctorTemplate(docId: number) {
  const doc = allDoctors.value.find(d => d.id === docId)
  templateDoctorId.value = docId
  templateDoctorName.value = doc?.name ?? ''
  templateIsDefault.value = false
  templatePanelVisible.value = true
}

function openDefaultTemplate() {
  templateDoctorId.value = null
  templateDoctorName.value = ''
  templateIsDefault.value = true
  templatePanelVisible.value = true
}

async function onTemplateSaved(action: 'now' | 'next') {
  templatePanelVisible.value = false
  if (action === 'now') {
    if (selectedDeptId.value) {
      const { start, end } = getWeekRange(weekStart.value)
      try {
        await doctorSchedulesApi.reapplyTemplate({
          department_id: selectedDeptId.value,
          work_date_from: formatDateStr(start),
          work_date_to: formatDateStr(end),
        })
        ElMessage.success('模板已应用')
      } catch (e: any) {
        ElMessage.error(e.response?.data?.detail || '应用模板失败')
      }
    }
  } else {
    ElMessage.success('模板将于下周生效')
  }
  await loadTemplateInfo()
  await fetchSchedules()
}

// ========== 单元格交互 ==========
function onCellClick(doctorId: number, date: string) {
  const doc = deptDoctors.value.find(d => d.id === doctorId)
  editingDoctorId.value = doctorId
  editingDoctorName.value = doc?.name ?? ''
  editingDate.value = date
  panelVisible.value = true
}

function onCellMouseDown(doctorId: number, date: string) {
  isDragging = true
  dragStartDoctorId = doctorId
  dragStartDate = date
  selectedCells.value = [{ doctorId, date }]
}

function onCellMouseEnter(doctorId: number, date: string) {
  if (!isDragging) return
  // 计算矩形选区
  const cells: Array<{ doctorId: number; date: string }> = []
  const docIds = deptDoctors.value.map(d => d.id)
  const startIdx = docIds.indexOf(dragStartDoctorId)
  const endIdx = docIds.indexOf(doctorId)
  const dateStartIdx = weekDates.value.indexOf(dragStartDate)
  const dateEndIdx = weekDates.value.indexOf(date)
  if (startIdx === -1 || endIdx === -1 || dateStartIdx === -1 || dateEndIdx === -1) return

  const rStart = Math.min(startIdx, endIdx)
  const rEnd = Math.max(startIdx, endIdx)
  const cStart = Math.min(dateStartIdx, dateEndIdx)
  const cEnd = Math.max(dateStartIdx, dateEndIdx)

  for (let r = rStart; r <= rEnd; r++) {
    for (let c = cStart; c <= cEnd; c++) {
      cells.push({ doctorId: docIds[r], date: weekDates.value[c] })
    }
  }
  selectedCells.value = cells
}

function onCellMouseUp() {
  if (isDragging && selectedCells.value.length > 1) {
    // 多选 → 打开面板批量排班
    editingDoctorId.value = selectedCells.value[0].doctorId
    const doc = deptDoctors.value.find(d => d.id === editingDoctorId.value)
    editingDoctorName.value = doc?.name ?? ''
    editingDate.value = selectedCells.value[0].date
    panelVisible.value = true
  }
  isDragging = false
}

// ========== 批量操作 ==========
async function fillAll(type: 'morning' | 'afternoon' | 'full') {
  if (!selectedDeptId.value) return
  const p = schedulePeriods.value
  const timeSlots: Array<{ start: string; end: string }> = []
  if (type === 'morning' || type === 'full') timeSlots.push({ start: p.morning.start, end: p.morning.end })
  if (type === 'afternoon' || type === 'full') timeSlots.push({ start: p.afternoon.start, end: p.afternoon.end })
  if (type === 'full') timeSlots.push({ start: p.evening.start, end: p.evening.end })
  try {
    await ElMessageBox.confirm(`确定给当前科室所有医生排满本周的${type === 'morning' ? '上午' : type === 'afternoon' ? '下午' : '全天'}吗？`)
    let count = 0
    for (const doc of deptDoctors.value) {
      for (const date of weekDates.value) {
        for (const slot of timeSlots) {
          const exists = schedules.value.some(
            s => s.doctor_id === doc.id && s.work_date === date &&
                 s.start_time.substring(0, 5) === slot.start &&
                 s.end_time.substring(0, 5) === slot.end
          )
          if (!exists) {
            await doctorSchedulesApi.createSchedule({
              doctor_id: doc.id,
              work_date: date,
              start_time: slot.start,
              end_time: slot.end,
              max_patients: 20,
            })
            count++
          }
        }
      }
    }
    ElMessage.success(`已创建 ${count} 条排班`)
    fetchSchedules()
  } catch { /* 取消 */ }
}

function onSaved() {
  panelVisible.value = false
  ElMessage.info('此修改仅影响当天，如需永久调整请修改模板')
  fetchSchedules()
}

</script>
