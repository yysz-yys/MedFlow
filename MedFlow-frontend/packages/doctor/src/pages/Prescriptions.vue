<template>
  <div class="page">
    <el-button type="primary" @click="openCreateDialog" style="margin-bottom:16px">开处方</el-button>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="患者" width="120">
        <template #default="{ row }">{{ row.patient_id }}</template>
      </el-table-column>
      <el-table-column label="药品数量" width="80">
        <template #default="{ row }">{{ row.items?.length || 0 }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 开处方弹窗 -->
    <el-dialog v-model="createDialogVisible" title="开处方" width="700px">
      <el-form :model="prescriptionForm" label-width="100px">
        <el-form-item label="诊断记录ID">
          <el-select v-model="prescriptionForm.diagnosis_id" placeholder="选择诊断记录" style="width:100%">
            <el-option v-for="d in diagnosisList" :key="d.id" :label="`诊断 #${d.id}`" :value="d.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-for="(item, idx) in prescriptionItems" :key="idx" style="border:1px solid #eee;padding:12px;margin-bottom:12px;border-radius:4px">
        <el-form :model="item" label-width="60px" inline>
          <el-form-item label="药品">
            <el-select v-model="item.drug_id" placeholder="选择药品" @change="(val: number) => onDrugChange(idx, val)" style="width:220px">
              <el-option v-for="d in drugList" :key="d.id" :label="`${d.name} (库存:${d.stock})`" :value="d.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="数量">
            <el-input-number v-model="item.quantity" :min="1" style="width:120px" />
          </el-form-item>
          <el-form-item label="用法">
            <el-input v-model="item.usage_method" placeholder="用法" style="width:140px" />
          </el-form-item>
          <el-form-item label="天数">
            <el-input-number v-model="item.days" :min="1" style="width:120px" />
          </el-form-item>
          <el-button type="danger" @click="removeItem(idx)">删除</el-button>
        </el-form>
      </div>
      <el-button @click="addItem" style="margin-bottom:12px">+ 添加药品</el-button>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreatePrescription">提交处方</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="处方详情" width="600px">
      <el-table :data="detailItems" border stripe>
        <el-table-column prop="drug_name" label="药品" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="usage_method" label="用法" />
        <el-table-column prop="days" label="天数" width="80" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { prescriptionsApi, diagnosisRecordsApi, drugsApi } from '@medflow/shared'
import type { Prescription, Drug, DiagnosisRecord } from '@medflow/shared'

const list = ref<Prescription[]>([])
const drugList = ref<Drug[]>([])
const diagnosisList = ref<DiagnosisRecord[]>([])
const loading = ref(false)
const submitting = ref(false)
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const detailItems = ref<Prescription['items']>([])

const prescriptionForm = reactive({
  diagnosis_id: null as number | null,
})

interface PrescriptionItemForm {
  drug_id: number | null
  quantity: number
  usage_method: string
  days: number
}

const prescriptionItems = ref<PrescriptionItemForm[]>([])

async function fetchData() {
  loading.value = true
  try {
    const [prescriptions, drugs, diagnoses] = await Promise.all([
      prescriptionsApi.listPrescriptions(),
      drugsApi.listDrugs(),
      diagnosisRecordsApi.listDiagnosisRecords(),
    ])
    list.value = prescriptions.data
    drugList.value = drugs.data
    diagnosisList.value = diagnoses.data
  } finally { loading.value = false }
}

function openCreateDialog() {
  prescriptionForm.diagnosis_id = null
  prescriptionItems.value = [{ drug_id: null, quantity: 1, usage_method: '', days: 1 }]
  createDialogVisible.value = true
}

function addItem() {
  prescriptionItems.value.push({ drug_id: null, quantity: 1, usage_method: '', days: 1 })
}

function removeItem(idx: number) {
  prescriptionItems.value.splice(idx, 1)
}

function onDrugChange(idx: number, val: number) {
  // auto-fill could go here
}

async function handleCreatePrescription() {
  if (!prescriptionForm.diagnosis_id) { ElMessage.warning('请选择诊断记录'); return }
  const items = prescriptionItems.value.filter(i => i.drug_id)
  if (items.length === 0) { ElMessage.warning('请添加至少一种药品'); return }
  submitting.value = true
  try {
    await prescriptionsApi.createPrescription({
      diagnosis_id: prescriptionForm.diagnosis_id,
      items: items.map(i => ({
        drug_id: i.drug_id!,
        quantity: i.quantity,
        usage_method: i.usage_method || undefined,
        days: i.days || undefined,
      })),
    })
    ElMessage.success('处方已创建')
    createDialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '创建失败') }
  finally { submitting.value = false }
}

function viewDetail(row: Prescription) {
  detailItems.value = row.items || []
  detailDialogVisible.value = true
}

onMounted(fetchData)
</script>
