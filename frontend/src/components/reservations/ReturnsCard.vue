<script setup lang="ts">
import { Printer } from '@lucide/vue'
import { NButton, NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'
import { allocationCode, allocationModel } from '@/utils/reservations'

/** What came back when, with the notes taken at the return. */
const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()
const { dateTime } = useFormat()

const returns = computed(() => {
  const allocations = props.reservation.items.flatMap((item) => item.allocations)
  return props.reservation.returns.map((r) => ({
    ...r,
    allocations: allocations.filter((a) => a.device_return === r.id),
  }))
})
</script>

<template>
  <NCard :title="t('reservations.returning.title')" size="small">
    <template #header-extra>
      <RouterLink
        :to="{ name: 'handover-protocol', params: { id: reservation.id } }"
        target="_blank"
      >
        <NButton size="tiny" quaternary>
          <template #icon><Printer :size="14" /></template>
          {{ t('handover.protocol') }}
        </NButton>
      </RouterLink>
    </template>
    <section v-for="r in returns" :key="r.id" class="return">
      <div class="head">
        <span class="mono">{{ dateTime(r.returned_at) }}</span>
        <span class="muted">{{ r.returned_by?.display_name ?? '—' }}</span>
      </div>
      <ul>
        <li v-for="a in r.allocations" :key="a.id">
          <span class="mono">{{ allocationCode(a) }}</span>
          <span>{{ allocationModel(a) }}</span>
          <span v-if="a.returned_damaged" class="warn">{{
            t('reservations.returning.damaged')
          }}</span>
          <span v-if="a.return_note" class="note">{{ a.return_note }}</span>
        </li>
      </ul>
      <p v-if="r.notes" class="muted small">{{ r.notes }}</p>
    </section>
  </NCard>
</template>

<style scoped>
.return + .return {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--ar-border);
}
.head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}
ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
li {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  padding: 4px 8px;
  border-left: 2px solid var(--ar-border);
  background: var(--ar-surface-sunken);
  margin-bottom: 3px;
}
.note,
.warn {
  color: var(--ar-warning);
  font-size: 11.5px;
}
.small {
  font-size: 11.5px;
  margin: 6px 0 0;
}
</style>
