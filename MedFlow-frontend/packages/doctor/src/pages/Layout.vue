<template>
  <AppLayout
    logo="云诊易 · 医生工作站"
    :menu-items="doctorMenu"
    :show-notification-bell="true"
    avatar-color="#67c23a"
    aside-color="#153d45"
  />
</template>

<script setup lang="ts">
import { AppLayout } from '@medflow/shared'
import { doctorMenu } from '../router/menu'
</script>
