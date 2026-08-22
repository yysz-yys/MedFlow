<template>
  <div class="personnel-page">
    <el-tabs v-model="activeTab" class="personnel-tabs" @tab-change="onTabChange">
      <el-tab-pane label="用户管理" name="users" />
      <el-tab-pane label="医生管理" name="doctors" />
      <el-tab-pane label="病人管理" name="patients" />
    </el-tabs>

    <Users v-if="activeTab === 'users'" :key="tabKey" />
    <Doctors v-else-if="activeTab === 'doctors'" :key="tabKey" />
    <Patients v-else-if="activeTab === 'patients'" :key="tabKey" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Users from './Users.vue'
import Doctors from './Doctors.vue'
import Patients from './Patients.vue'

const activeTab = ref('users')
const tabKey = ref(0)

function onTabChange() {
  tabKey.value++
}
</script>

<style scoped>
.personnel-page {
  background: #fff;
  border-radius: 4px;
  padding: 0 20px 20px;
}

.personnel-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.personnel-tabs :deep(.el-tabs__item) {
  font-size: 15px;
}
</style>
