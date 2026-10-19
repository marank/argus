<script setup lang="ts">
import { Printer } from '@lucide/vue'
import { NButton, NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()
const { dateTime, enumLabel } = useFormat()

const handover = computed(() => props.reservation.handover!)
const deviceNotes = computed(() =>
  props.reservation.items
    .flatMap((item) => item.allocations)
    .filter((a) => a.handout_note)
    .map((a) => ({
      id: a.id,
      label: a.asset?.inventory_number ?? a.consumable?.model.full_name,
      note: a.handout_note,
    })),
)

const entries = computed<DetailEntry[]>(() => {
  const h = handover.value
  return [
    { label: t('handover.method'), value: enumLabel('handoverMethod', h.method) },
    { label: t('handover.receivedBy'), value: h.received_by_name },
    { label: t('handover.handedOutAt'), value: dateTime(h.handed_out_at), mono: true },
    { label: t('handover.handedOutBy'), value: h.handed_out_by?.display_name },
    ...(h.location ? [{ label: t('handover.deliveredTo'), value: h.location }] : []),
    ...(h.notes ? [{ label: t('common.notes'), value: h.notes, wide: true }] : []),
  ]
})
</script>

<template>
  <NCard :title="t('handover.title')" size="small">
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
    <DetailGrid :entries="entries" />
    <ul v-if="deviceNotes.length" class="notes">
      <li v-for="n in deviceNotes" :key="n.id">
        <span class="mono">{{ n.label }}</span> {{ n.note }}
      </li>
    </ul>
    <figure v-if="handover.signature" class="signature">
      <img :src="handover.signature" :alt="t('handover.signature')" />
      <figcaption class="eyebrow">
        {{ t('handover.signature') }} · {{ handover.received_by_name }}
      </figcaption>
    </figure>
  </NCard>
</template>

<style scoped>
.notes {
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}
.notes li {
  padding: 4px 8px;
  border-left: 2px solid var(--ar-warning);
  background: var(--ar-surface-sunken);
  margin-bottom: 3px;
}
.signature {
  margin: 14px 0 0;
}
.signature img {
  display: block;
  max-width: 100%;
  height: 110px;
  object-fit: contain;
  padding: 6px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: #fff;
}
.signature figcaption {
  margin-top: 4px;
}
</style>
