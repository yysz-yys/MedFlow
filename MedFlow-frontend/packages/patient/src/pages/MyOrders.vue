<template>
  <div class="page">
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索药品或医生"
        clearable
        :prefix-icon="Search"
        style="width:240px"
      />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width:110px">
        <el-option label="待取药" :value="1" />
        <el-option label="已取药" :value="2" />
        <el-option label="已取消" :value="0" />
      </el-select>
    </div>

    <el-table :data="sortedList" border stripe v-loading="loading" @sort-change="handleSortChange">
      <el-table-column prop="id" label="ID" width="70" sortable="custom" />
      <el-table-column prop="drugName" label="药品名称" min-width="140" sortable="custom">
        <template #default="{ row }">{{ drugNames[row.prescription_id] || '-' }}</template>
      </el-table-column>
      <el-table-column prop="doctor_name" label="开方医生" min-width="100" sortable="custom" />
      <el-table-column prop="total_amount" label="金额(元)" min-width="90" sortable="custom" />
      <el-table-column prop="status" label="状态" width="100" sortable="custom">
        <template #default="{ row }">
          <el-tag :type="row.status === 2 ? 'success' : row.status === 0 ? 'danger' : 'warning'">
            {{ row.status === 0 ? '已取消' : row.status === 1 ? '待取药' : '已取药' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="210">
        <template #default="{ row }">
          <template v-if="row.status === 1">
            <el-button size="small" type="success" @click="handleComplete(row)">取药</el-button>
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <el-button size="small" type="danger" @click="handleCancel(row)">取消</el-button>
          </template>
          <template v-else-if="row.status === 2">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <el-button size="small" @click="handleUncomplete(row)">撤回</el-button>
          </template>
          <template v-else-if="row.status === 0">
            <el-button size="small" type="primary" @click="handleRestore(row)">恢复</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="订单详情" width="600px">
      <el-table :data="detailItems" border stripe size="small" v-loading="detailLoading">
        <el-table-column prop="drug_name" label="药品名称" />
        <el-table-column prop="specification" label="规格" width="120" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column prop="quantity" label="数量" width="60" />
        <el-table-column prop="days" label="天数" width="60">
          <template #default="{ row }">{{ row.days ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="usage_method" label="用法" width="160">
          <template #default="{ row }">{{ row.usage_method || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { drugOrdersApi, prescriptionsApi, formatDateTime } from '@medflow/shared'
import type { DrugOrder, PrescriptionItem } from '@medflow/shared'

const list = ref<DrugOrder[]>([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref<number | undefined>(undefined)
const drugNames = ref<Record<number, string>>({})
const sortBy = ref('')
const sortOrder = ref('')

const filteredList = computed(() => {
  let result = list.value
  if (statusFilter.value != null) {
    result = result.filter(o => o.status === statusFilter.value)
  }
  const kw = keyword.value.trim().toLowerCase()
  if (kw) {
    result = result.filter(o =>
      (o.doctor_name || '').toLowerCase().includes(kw) ||
      (drugNames.value[o.prescription_id] || '').toLowerCase().includes(kw)
    )
  }
  return result
})

const sortedList = computed(() => {
  const result = [...filteredList.value]
  if (!sortBy.value) return result
  result.sort((a: any, b: any) => {
    let va = a[sortBy.value]
    let vb = b[sortBy.value]
    if (sortBy.value === 'drugName') {
      va = drugNames.value[a.prescription_id] || ''
      vb = drugNames.value[b.prescription_id] || ''
    }
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    if (typeof va === 'string') {
      return sortOrder.value === 'desc' ? vb.localeCompare(va) : va.localeCompare(vb)
    }
    return sortOrder.value === 'desc' ? vb - va : va - vb
  })
  return result
})
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailItems = ref<PrescriptionItem[]>([])

async function fetchData() {
  loading.value = true
  try {
    const res = await drugOrdersApi.listDrugOrders()
    list.value = res.data
    const rxs = await prescriptionsApi.listPrescriptions()
    const map: Record<number, string> = {}
    for (const rx of rxs.data) {
      map[rx.id] = (rx.items || []).map(i => i.drug_name).join('、') || '-'
    }
    drugNames.value = map
  } finally { loading.value = false }
}

function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortBy.value = order ? prop : ''
  sortOrder.value = order ? (order.startsWith('asc') ? 'asc' : 'desc') : ''
}

async function openDetail(row: DrugOrder) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await prescriptionsApi.getPrescription(row.prescription_id)
    detailItems.value = res.data.items || []
  } catch {
    detailItems.value = []
  } finally {
    detailLoading.value = false
  }
}

async function handleCancel(row: DrugOrder) {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？库存将退还。', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await drugOrdersApi.cancelOrder(row.id)
    ElMessage.success('订单已取消')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleComplete(row: DrugOrder) {
  try {
    await ElMessageBox.confirm('确定标记为已取药吗？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await drugOrdersApi.completeOrder(row.id)
    ElMessage.success('已取药')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleRestore(row: DrugOrder) {
  try {
    await ElMessageBox.confirm('确定要恢复该订单吗？将重新扣减库存。', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await drugOrdersApi.restoreOrder(row.id)
    ElMessage.success('订单已恢复')
    fetchData()
  } catch { /* 取消 */ }
}

async function handleUncomplete(row: DrugOrder) {
  try {
    await ElMessageBox.confirm('确定要撤回取药确认吗？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await drugOrdersApi.uncompleteOrder(row.id)
    ElMessage.success('已撤回')
    fetchData()
  } catch { /* 取消 */ }
}

onMounted(fetchData)
</script>

<style scoped>
.search-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 10px;
}
</style>
