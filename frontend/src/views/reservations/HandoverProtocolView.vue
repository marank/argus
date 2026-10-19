<script setup lang="ts">
import type { Id } from '@/types/common'
import { Printer } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

/** Printable handover record (A4), opened from the reservation in a new tab. */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const { date, dateTime, enumLabel } = useFormat()
const reservation = ref<Reservation | null>(null)

onMounted(async () => (reservation.value = await reservationsApi.get(props.id)))

const print = () => window.print()

const rows = computed(() =>
  (reservation.value?.items ?? []).flatMap((item) =>
    item.allocations.map((a) => ({
      id: a.id,
      number: a.asset?.inventory_number ?? '',
      model: a.asset?.model.full_name ?? a.stock_item?.model.full_name ?? item.label,
      serial: a.asset?.serial_number ?? '',
      quantity: a.quantity,
      note: a.handout_note,
    })),
  ),
)
</script>

<template>
  <div v-if="reservation" class="toolbar">
    <NButton type="primary" @click="print">
      <template #icon><Printer :size="16" /></template>
      {{ t('handover.print') }}
    </NButton>
  </div>
  <div v-if="reservation" class="sheet">
    <header>
      <div>
        <div class="brand mono">ARGUS</div>
        <h1>{{ t('handover.protocol') }}</h1>
      </div>
      <div class="mono right">
        <div>{{ reservation.number }}</div>
        <div>{{ reservation.handover ? dateTime(reservation.handover.handed_out_at) : '—' }}</div>
      </div>
    </header>

    <dl class="facts">
      <div>
        <dt>{{ t('reservations.requester') }}</dt>
        <dd>{{ reservation.requester.display_name }}</dd>
      </div>
      <div>
        <dt>{{ t('reservations.department') }}</dt>
        <dd>{{ reservation.department?.name ?? '—' }}</dd>
      </div>
      <div>
        <dt>{{ t('reservations.purpose') }}</dt>
        <dd>{{ reservation.title }}</dd>
      </div>
      <div>
        <dt>{{ t('reservations.period') }}</dt>
        <dd>
          {{ date(reservation.start_date) }} →
          {{ reservation.end_date ? date(reservation.end_date) : t('common.permanent') }}
        </dd>
      </div>
      <template v-if="reservation.handover">
        <div>
          <dt>{{ t('handover.method') }}</dt>
          <dd>{{ enumLabel('handoverMethod', reservation.handover.method) }}</dd>
        </div>
        <div>
          <dt>{{ t('handover.receivedBy') }}</dt>
          <dd>{{ reservation.handover.received_by_name }}</dd>
        </div>
        <div>
          <dt>{{ t('handover.handedOutBy') }}</dt>
          <dd>{{ reservation.handover.handed_out_by?.display_name ?? '—' }}</dd>
        </div>
        <div v-if="reservation.handover.location">
          <dt>{{ t('handover.deliveredTo') }}</dt>
          <dd>{{ reservation.handover.location }}</dd>
        </div>
      </template>
    </dl>

    <table>
      <thead>
        <tr>
          <th>{{ t('inventory.fields.inventoryNumber') }}</th>
          <th>{{ t('inventory.fields.model') }}</th>
          <th>{{ t('inventory.fields.serialNumber') }}</th>
          <th class="num">{{ t('common.quantity') }}</th>
          <th>{{ t('common.notes') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td class="mono">{{ row.number }}</td>
          <td>{{ row.model }}</td>
          <td class="mono">{{ row.serial }}</td>
          <td class="num mono">{{ row.quantity }}</td>
          <td>{{ row.note }}</td>
        </tr>
      </tbody>
    </table>

    <p v-if="reservation.handover?.notes" class="notes">{{ reservation.handover.notes }}</p>

    <section class="sign">
      <div class="signature">
        <img v-if="reservation.handover?.signature" :src="reservation.handover.signature" alt="" />
        <div class="line" />
        <span>{{ t('handover.signature') }} · {{ reservation.handover?.received_by_name }}</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.sheet {
  max-width: 820px;
  margin: 12px auto 24px;
  padding: 40px 48px;
  background: #fff;
  color: #0b1220;
  font-size: 13px;
}
.toolbar {
  display: flex;
  justify-content: flex-end;
  max-width: 820px;
  margin: 24px auto 0;
}
header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-bottom: 14px;
  border-bottom: 2px solid #0b1220;
}
.brand {
  letter-spacing: 0.3em;
  font-weight: 700;
  color: #0e7490;
}
h1 {
  margin: 4px 0 0;
  font-size: 22px;
}
.right {
  text-align: right;
}
.facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 32px;
  margin: 22px 0;
}
dt {
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #5b6877;
}
dd {
  margin: 2px 0 0;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 6px 8px;
  border-bottom: 1px solid #d5dbe1;
  text-align: left;
}
th {
  font-size: 11px;
  color: #5b6877;
}
.num {
  text-align: right;
}
.notes {
  margin: 16px 0 0;
  white-space: pre-line;
}
.sign {
  margin-top: 48px;
}
.signature {
  width: 320px;
}
.signature img {
  display: block;
  height: 90px;
  max-width: 100%;
  object-fit: contain;
}
.line {
  border-bottom: 1px solid #0b1220;
  margin-bottom: 4px;
}
@media print {
  .toolbar {
    display: none;
  }
  .sheet {
    margin: 0;
    padding: 0;
  }
}
</style>
