<script setup lang="ts">
import { LayoutDashboard } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import EmployeeDashboard from '@/components/dashboard/EmployeeDashboard.vue'
import ItDashboard from '@/components/dashboard/ItDashboard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'

const { t, d } = useI18n()
const auth = useAuthStore()
const editing = ref(false)
</script>

<template>
  <div class="page">
    <PageHeader
      :eyebrow="d(new Date(), 'weekday')"
      :title="t('dashboard.greeting', { name: auth.user?.first_name || auth.user?.username })"
      :subtitle="auth.isItStaff ? t('dashboard.itSubtitle') : t('dashboard.employeeSubtitle')"
    >
      <template v-if="auth.isItStaff && !editing" #actions>
        <NButton size="small" @click="editing = true">
          <template #icon><LayoutDashboard /></template>
          {{ t('dashboard.edit.open') }}
        </NButton>
      </template>
    </PageHeader>
    <ItDashboard v-if="auth.isItStaff" v-model:editing="editing" />
    <EmployeeDashboard v-else />
  </div>
</template>
