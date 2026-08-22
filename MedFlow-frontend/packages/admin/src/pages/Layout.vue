<template>
  <AppLayout
    logo="云诊易 · 管理后台"
    :menu-items="adminMenu"
  />
</template>

<script setup lang="ts">
import { AppLayout } from '@medflow/shared'
import { adminMenu } from '../router/menu'
</script>
