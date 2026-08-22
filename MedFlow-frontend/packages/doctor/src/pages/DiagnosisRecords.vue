<template>
  <div class="page">
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索患者姓名"
        clearable
        style="width: 240px"
        @input="onSearchInput"
        @keyup.enter="page = 1"
      />
    </div>

    <el-table :data="pagedList" border stripe v-loading="loading" :row-style="{ height: '44px' }">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="患者" width="120">
        <template #default="{ row }">{{ row.patient_name || row.patient_id }}</template>
      </el-table-column>
      <el-table-column prop="diagnosis_result" label="诊断结果" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 19) || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openView(row)">查看</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">修改</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :total="total"
      :page-size="pageSize"
      background
      layout="total, prev, pager, next"
      style="margin-top:20px;justify-content:flex-end"
    />

    <!-- 查看弹窗（只读，左右布局） -->
    <el-dialog v-model="viewVisible" :title="`诊断详情 · ${viewForm.patient_name}`" width="860px">
      <el-form :model="viewForm" label-width="80px">
        <el-form-item label="挂号ID">
          <el-input :model-value="viewForm.appointment_id" disabled />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <div class="col-title">诊断信息</div>

            <el-form-item label="主诉">
              <el-input :model-value="viewForm.chief_complaint" type="textarea" :rows="3" disabled />
            </el-form-item>
            <el-form-item label="诊断结果">
              <el-input :model-value="viewForm.diagnosis_result" type="textarea" :rows="4" disabled />
            </el-form-item>
            <el-form-item label="处方建议">
              <el-input :model-value="viewForm.prescription_advice" type="textarea" :rows="3" disabled />
            </el-form-item>
            <el-form-item label="创建时间">
              <el-input :model-value="viewForm.created_at" disabled />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <div class="col-title">处方用药</div>

            <el-table v-if="viewRxItems.length" :data="viewRxItems" border size="small">
              <el-table-column prop="drug_name" label="药品" />
              <el-table-column prop="quantity" label="数量" width="50" />
              <el-table-column prop="days" label="天数" width="50" />
              <el-table-column prop="usage_method" label="用法" />
            </el-table>
            <el-empty v-else description="未开处方" />
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 修改弹窗（可编辑，左右布局） -->
    <el-dialog v-model="editVisible" :title="`修改诊断 · ${editPatientName}`" width="860px">
      <el-form label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="col-title">诊断信息</div>

            <el-form-item label="主诉">
              <el-input v-model="editForm.chief_complaint" type="textarea" :rows="3" placeholder="患者主诉" />
            </el-form-item>
            <el-form-item label="诊断结果">
              <el-input v-model="editForm.diagnosis_result" type="textarea" :rows="4" placeholder="诊断结果" />
            </el-form-item>
            <el-form-item label="处方建议">
              <el-input v-model="editForm.prescription_advice" type="textarea" :rows="3" placeholder="处方建议" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <div class="col-title">处方用药</div>

            <div style="margin-bottom:8px">
              <el-button size="small" type="primary" @click="addEditRxItem">+ 添加药品</el-button>
            </div>
            <div class="rx-scroll">
              <div
                v-for="(item, idx) in editRxItems"
                :key="idx"
                style="border:1px solid #ebeef5;border-radius:4px;padding:8px 10px;margin-bottom:8px"
              >
                <el-row :gutter="6" align="middle" style="margin-bottom:6px">
                  <el-col :span="4" style="font-size:13px;color:#606266">药品</el-col>
                  <el-col :span="16">
                    <el-select v-model="item.drug_id" placeholder="选择药品" clearable style="width:100%" size="small">
                      <el-option v-for="d in drugList" :key="d.id" :label="`${d.name} · ${d.specification || '-'} · ${d.unit || '-'} (库存:${d.stock})`" :value="d.id" />
                    </el-select>
                  </el-col>
                  <el-col :span="4" style="text-align:right">
                    <el-button size="small" type="danger" @click="removeEditRxItem(idx)" :disabled="editRxItems.length === 1" text>删除</el-button>
                  </el-col>
                </el-row>
                <el-row :gutter="6" align="middle" style="margin-bottom:6px">
                  <el-col :span="4" style="font-size:13px;color:#606266">数量</el-col>
                  <el-col :span="8">
                    <el-input-number v-model="item.quantity" :min="1" size="small" style="width:100%" />
                  </el-col>
                  <el-col :span="4" style="font-size:13px;color:#606266">天数</el-col>
                  <el-col :span="8">
                    <el-input-number v-model="item.days" :min="1" size="small" style="width:100%" />
                  </el-col>
                </el-row>
                <el-row :gutter="6" align="middle">
                  <el-col :span="4" style="font-size:13px;color:#606266">用法</el-col>
                  <el-col :span="20">
                    <el-input v-model="item.usage_method" placeholder="限100字" maxlength="100" size="small" />
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleEditSave">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { diagnosisRecordsApi, prescriptionsApi, drugsApi } from '@medflow/shared'
import type { DiagnosisRecord, Drug, Prescription } from '@medflow/shared'

const list = ref<DiagnosisRecord[]>([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = 10

const filteredList = computed(() => {
  if (!keyword.value.trim()) return list.value
  const kw = keyword.value.trim().toLowerCase()
  return list.value.filter(r =>
    (r.patient_name || '').toLowerCase().includes(kw)
  )
})

const total = computed(() => filteredList.value.length)

const pagedList = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredList.value.slice(start, start + pageSize)
})

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1 }, 300)
}

// ---- 查看弹窗 ----
const viewVisible = ref(false)
const viewForm = reactive({
  patient_name: '',
  appointment_id: null as number | null,
  chief_complaint: '',
  diagnosis_result: '',
  prescription_advice: '',
  created_at: '',
})
const viewRxItems = ref<{ drug_name: string; quantity: number; days: number; usage_method: string }[]>([])

async function openView(row: DiagnosisRecord) {
  viewForm.patient_name = row.patient_name || String(row.patient_id)
  viewForm.appointment_id = row.appointment_id
  viewForm.chief_complaint = row.chief_complaint || '-'
  viewForm.diagnosis_result = row.diagnosis_result || '-'
  viewForm.prescription_advice = row.prescription_advice || '-'
  viewForm.created_at = row.created_at?.replace('T', ' ').slice(0, 19) || '-'

  // 查询关联处方
  try {
    const res = await prescriptionsApi.listPrescriptions()
    const pList = (res.data as Prescription[]).filter(p => p.diagnosis_id === row.id)
    viewRxItems.value = pList.length > 0
      ? pList[0].items.map(i => ({
          drug_name: i.drug_name,
          quantity: i.quantity,
          days: i.days || 0,
          usage_method: i.usage_method || '',
        }))
      : []
  } catch { viewRxItems.value = [] }

  viewVisible.value = true
}

// ---- 修改弹窗 ----
const editVisible = ref(false)
const editSubmitting = ref(false)
const editId = ref<number | null>(null)
const editPatientName = ref('')
const editForm = reactive({
  chief_complaint: '',
  diagnosis_result: '',
  prescription_advice: '',
})

interface EditRxItem {
  drug_id: number | null
  quantity: number
  days: number
  usage_method: string
}
const editRxItems = ref<EditRxItem[]>([])
const editPrescriptionId = ref<number | null>(null)
const drugList = ref<Drug[]>([])

async function loadDrugList() {
  if (drugList.value.length > 0) return
  try {
    const res = await drugsApi.listDrugs({ page_size: 999, status: 0 })
    drugList.value = res.data.items
  } catch { /* ignore */ }
}

function addEditRxItem() {
  editRxItems.value.push({ drug_id: null, quantity: 1, days: 1, usage_method: '' })
}

function removeEditRxItem(idx: number) {
  if (editRxItems.value.length > 1) editRxItems.value.splice(idx, 1)
}

async function openEdit(row: DiagnosisRecord) {
  editId.value = row.id
  editPatientName.value = row.patient_name || String(row.patient_id)
  editForm.chief_complaint = row.chief_complaint || ''
  editForm.diagnosis_result = row.diagnosis_result || ''
  editForm.prescription_advice = row.prescription_advice || ''

  await loadDrugList()

  // 查询关联处方并回填
  try {
    const res = await prescriptionsApi.listPrescriptions()
    const pList = (res.data as Prescription[]).filter(p => p.diagnosis_id === row.id)
    if (pList.length > 0) {
      editPrescriptionId.value = pList[0].id
      editRxItems.value = pList[0].items.map(i => ({
        drug_id: i.drug_id,
        quantity: i.quantity,
        days: i.days || 1,
        usage_method: i.usage_method || '',
      }))
    } else {
      editPrescriptionId.value = null
      editRxItems.value = [{ drug_id: null, quantity: 1, days: 1, usage_method: '' }]
    }
  } catch {
    editPrescriptionId.value = null
    editRxItems.value = [{ drug_id: null, quantity: 1, days: 1, usage_method: '' }]
  }

  editVisible.value = true
}

async function handleEditSave() {
  if (!editId.value) return
  editSubmitting.value = true
  try {
    await diagnosisRecordsApi.updateDiagnosisRecord(editId.value, {
      chief_complaint: editForm.chief_complaint || undefined,
      diagnosis_result: editForm.diagnosis_result || undefined,
      prescription_advice: editForm.prescription_advice || undefined,
    })

    // 保存处方
    const filled = editRxItems.value.filter(i => i.drug_id)
    if (filled.length > 0) {
      if (editPrescriptionId.value) {
        await prescriptionsApi.updatePrescription(editPrescriptionId.value, filled.map(i => ({
          drug_id: i.drug_id!,
          quantity: i.quantity,
          usage_method: i.usage_method || undefined,
          days: i.days || undefined,
        })))
      } else {
        await prescriptionsApi.createPrescription({
          diagnosis_id: editId.value,
          items: filled.map(i => ({
            drug_id: i.drug_id!,
            quantity: i.quantity,
            usage_method: i.usage_method || undefined,
            days: i.days || undefined,
          })),
        })
      }
    }

    ElMessage.success('保存成功')
    editVisible.value = false
    fetchData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    editSubmitting.value = false
  }
}

// ---- 数据加载 ----
async function fetchData() {
  loading.value = true
  try {
    const res = await diagnosisRecordsApi.listDiagnosisRecords()
    list.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.search-bar {
  margin-bottom: 16px;
}

.col-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.rx-scroll {
  max-height: 340px;
  overflow-y: auto;
}
</style>
