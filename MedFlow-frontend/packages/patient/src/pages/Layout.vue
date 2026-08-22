<template>
  <AppLayout
    logo="云诊易 · 患者服务"
    :menu-items="patientMenu"
    :show-notification-bell="true"
    avatar-color="#f0a0b0"
    aside-color="#4a2d3d"
  />
</template>

<script setup lang="ts">
import { AppLayout } from '@medflow/shared'
import { patientMenu } from '../router/menu'
</script>
