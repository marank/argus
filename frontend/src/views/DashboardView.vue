<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import EmployeeDashboard from '@/components/dashboard/EmployeeDashboard.vue'
import ItDashboard from '@/components/dashboard/ItDashboard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'

const { t, d } = useI18n()
const auth = useAuthStore()
</script>

<template>
  <div class="page">
    <PageHeader
      :eyebrow="d(new Date(), 'weekday')"
      :title="t('dashboard.greeting', { name: auth.user?.first_name || auth.user?.username })"
      :subtitle="auth.isItStaff ? t('dashboard.itSubtitle') : t('dashboard.employeeSubtitle')"
    />
    <ItDashboard v-if="auth.isItStaff" />
    <EmployeeDashboard v-else />
  </div>
</template>
