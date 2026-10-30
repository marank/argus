<script setup lang="ts">
import { Printer } from '@lucide/vue'
import { NButton, NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { useFormat } from '@/composables/useFormat'
import { allocationCode, allocationModel } from '@/utils/requests'

/**
 * What came back when, with the notes taken at the return. `withDue` adds the
 * return date and the last reminder on top (IT's view).
 */
const props = withDefaults(
  defineProps<{
    assetRequest: Schemas['AssetRequestOut']
    withDue?: boolean
    printable?: boolean
  }>(),
  { printable: true },
)
const { t } = useI18n()
const { date, dateTime } = useFormat()

const due = computed<DetailEntry[]>(() => {
  const r = props.assetRequest
  return [
    { label: t('requests.detail.dueDate'), value: date(r.end_date), slot: 'due' },
    {
      label: t('requests.remindedAt'),
      value: r.reminded_at
        ? `${dateTime(r.reminded_at)} · ${r.reminded_by?.display_name ?? '—'}`
        : null,
    },
  ]
})

const returns = computed(() => {
  const allocations = props.assetRequest.items.flatMap((item) => item.allocations)
  return props.assetRequest.returns.map((r) => ({
    ...r,
    allocations: allocations.filter((a) => a.device_return === r.id),
  }))
})
</script>

<template>
  <NCard :title="t('requests.returning.title')" size="small">
    <template v-if="printable && assetRequest.returns.length" #header-extra>
      <RouterLink
        :to="{ name: 'handover-protocol', params: { id: assetRequest.id } }"
        target="_blank"
      >
        <NButton size="tiny" quaternary>
          <template #icon><Printer :size="14" /></template>
          {{ t('handover.protocol') }}
        </NButton>
      </RouterLink>
    </template>
    <DetailGrid v-if="withDue" :entries="due" :class="{ spaced: returns.length }">
      <template #due>
        <span class="mono">{{ date(assetRequest.end_date) }}</span>
        <span v-if="assetRequest.is_overdue" class="overdue"> · {{ t('requests.overdue') }}</span>
      </template>
    </DetailGrid>
    <section v-for="r in returns" :key="r.id" class="return">
      <div class="head">
        <span class="mono">{{ dateTime(r.returned_at) }}</span>
        <span class="muted">{{ r.returned_by?.display_name ?? '—' }}</span>
      </div>
      <ul>
        <li v-for="a in r.allocations" :key="a.id">
          <span class="mono">{{ allocationCode(a) }}</span>
          <span>{{ allocationModel(a) }}</span>
          <span v-if="a.returned_damaged" class="warn">{{ t('requests.returning.damaged') }}</span>
          <span v-if="a.return_note" class="note">{{ a.return_note }}</span>
        </li>
      </ul>
      <p v-if="r.notes" class="muted small">{{ r.notes }}</p>
    </section>
  </NCard>
</template>

<style scoped>
.spaced {
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--ar-border);
}
.overdue {
  color: var(--ar-error);
  font-weight: 600;
}
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
