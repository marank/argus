<script setup lang="ts">
import { LayoutDashboard, Plus, RotateCcw } from '@lucide/vue'
import { useIntervalFn } from '@vueuse/core'
import { NButton } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import EmployeeDashboard from '@/components/dashboard/EmployeeDashboard.vue'
import ItDashboard from '@/components/dashboard/ItDashboard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useFormat } from '@/composables/useFormat'
import { useAuthStore } from '@/stores/auth'

const { t, d } = useI18n()
const { longDate } = useFormat()

/** A running clock in the header: "Dienstag, 20. Oktober · 13:38" with a blinking colon. */
const now = ref(new Date())
useIntervalFn(() => (now.value = new Date()), 1000)
const clock = computed(() => {
  const time = d(now.value, 'time')
  const colon = time.indexOf(':')
  return {
    day: longDate(now.value),
    hours: time.slice(0, colon),
    minutes: time.slice(colon + 1),
  }
})
const auth = useAuthStore()
const editing = ref(false)
const dashboard = ref<InstanceType<typeof ItDashboard>>()
</script>

<template>
  <div class="page">
    <!-- While editing, the header becomes the editor bar: same lines, same height, no jump. -->
    <PageHeader
      v-if="editing"
      class="editing"
      :eyebrow="t('dashboard.edit.eyebrow')"
      :title="t('dashboard.edit.open')"
      :subtitle="t('dashboard.edit.hint')"
    >
      <template #actions>
        <NButton
          size="small"
          :disabled="!dashboard?.canAdd"
          :title="t('dashboard.edit.add')"
          @click="dashboard?.openPicker()"
        >
          <template #icon><Plus /></template>
          <span class="label">{{ t('dashboard.edit.add') }}</span>
        </NButton>
        <NButton
          size="small"
          quaternary
          :title="t('dashboard.edit.reset')"
          @click="dashboard?.reset()"
        >
          <template #icon><RotateCcw /></template>
          <span class="label">{{ t('dashboard.edit.reset') }}</span>
        </NButton>
        <NButton size="small" @click="editing = false">{{ t('common.cancel') }}</NButton>
        <NButton
          size="small"
          type="primary"
          :loading="dashboard?.saving"
          @click="dashboard?.save()"
        >
          {{ t('dashboard.edit.done') }}
        </NButton>
      </template>
    </PageHeader>
    <PageHeader
      v-else
      :title="t('dashboard.greeting', { name: auth.user?.first_name || auth.user?.username })"
      :subtitle="auth.isItStaff ? t('dashboard.itSubtitle') : t('dashboard.employeeSubtitle')"
    >
      <template #eyebrow>
        <time :datetime="now.toISOString()"
          >{{ clock.day }} · {{ clock.hours }}<span class="blink">:</span>{{ clock.minutes }}</time
        >
      </template>
      <template v-if="auth.isItStaff" #actions>
        <NButton size="small" @click="editing = true">
          <template #icon><LayoutDashboard /></template>
          {{ t('dashboard.edit.open') }}
        </NButton>
      </template>
    </PageHeader>
    <ItDashboard v-if="auth.isItStaff" ref="dashboard" v-model:editing="editing" />
    <EmployeeDashboard v-else />
  </div>
</template>

<style scoped>
/* The clock's colon changes once a second (a second on, a second off); not for those who reduce motion. */
.blink {
  animation: blink 2s steps(1, end) infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .blink {
    animation: none;
  }
}
/*
 * The tint is drawn behind the header, so it adds nothing to its size. It stays
 * in view while scrolling; the page colour above it covers the widgets passing.
 */
/* Stuck at the page's top padding (base.css), so it does not move when scrolling starts. */
.page-header.editing {
  position: sticky;
  top: 20px;
  z-index: 10;
  isolation: isolate;
}
.page-header.editing::before {
  content: '';
  position: absolute;
  inset: -10px -12px -1px;
  z-index: -1;
  border: 1px solid var(--ar-primary);
  border-radius: 3px;
  background: color-mix(in srgb, var(--ar-primary) 8%, var(--ar-surface));
  /* Covers the gap above it down to the top bar. */
  box-shadow: 0 -12px 0 0 var(--ar-bg);
}
@media (max-width: 720px) {
  .page-header.editing {
    top: 14px;
  }
}
.page-header.editing :deep(.eyebrow) {
  color: var(--ar-primary);
}
/* On phones the four buttons keep to one row, like the single button they replace. */
@media (max-width: 640px) {
  .page-header.editing .label {
    display: none;
  }
  .page-header.editing :deep(.n-button__icon) {
    margin: 0;
  }
}
</style>
