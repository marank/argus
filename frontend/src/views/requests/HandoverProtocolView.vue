<script setup lang="ts">
import type { Id } from '@/types/common'
import { Printer } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import { useFormat } from '@/composables/useFormat'
import type { AssetRequest } from '@/types/requests'
import { allocationModel } from '@/utils/requests'

/** Printable handover record (A4), opened from the request in a new tab. */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const { date, dateTime, enumLabel } = useFormat()
const assetRequest = ref<AssetRequest | null>(null)

onMounted(async () => (assetRequest.value = await requestsApi.get(props.id)))

const print = () => window.print()

const rows = computed(() =>
  (assetRequest.value?.items ?? []).flatMap((item) =>
    item.allocations.map((a) => ({
      id: a.id,
      number: a.asset?.inventory_number ?? a.license?.device?.inventory_number ?? '',
      model: allocationModel(a) || item.label,
      serial: a.asset?.serial_number ?? '',
      quantity: a.quantity,
      note: a.handout_note,
    })),
  ),
)

/** Each return with what came back, the note and whether it came back damaged. */
const returns = computed(() => {
  const allocations = (assetRequest.value?.items ?? []).flatMap((item) => item.allocations)
  return (assetRequest.value?.returns ?? []).map((r) => ({
    ...r,
    rows: allocations
      .filter((a) => a.device_return === r.id)
      .map((a) => ({
        id: a.id,
        number: a.asset?.inventory_number ?? a.license?.device?.inventory_number ?? '',
        model: allocationModel(a),
        serial: a.asset?.serial_number ?? '',
        damaged: a.returned_damaged,
        note: a.return_note,
      })),
  }))
})
</script>

<template>
  <div v-if="assetRequest" class="toolbar">
    <NButton type="primary" @click="print">
      <template #icon><Printer :size="16" /></template>
      {{ t('handover.print') }}
    </NButton>
  </div>
  <div v-if="assetRequest" class="sheet">
    <header>
      <div>
        <div class="brand mono">ARGUS</div>
        <h1>{{ t('handover.protocol') }}</h1>
      </div>
      <div class="mono right">
        <div>{{ assetRequest.number }}</div>
        <div>{{ assetRequest.handover ? dateTime(assetRequest.handover.handed_out_at) : '—' }}</div>
      </div>
    </header>

    <dl class="facts">
      <div>
        <dt>{{ t('requests.requester') }}</dt>
        <dd>{{ assetRequest.requester.display_name }}</dd>
      </div>
      <div>
        <dt>{{ t('requests.department') }}</dt>
        <dd>{{ assetRequest.department?.name ?? '—' }}</dd>
      </div>
      <div>
        <dt>{{ t('requests.purpose') }}</dt>
        <dd>{{ assetRequest.title }}</dd>
      </div>
      <div>
        <dt>{{ t('requests.period') }}</dt>
        <dd>
          {{ date(assetRequest.start_date) }} →
          {{ assetRequest.end_date ? date(assetRequest.end_date) : t('common.permanent') }}
        </dd>
      </div>
      <template v-if="assetRequest.handover">
        <div>
          <dt>{{ t('handover.method') }}</dt>
          <dd>{{ enumLabel('handoverMethod', assetRequest.handover.method) }}</dd>
        </div>
        <div>
          <dt>{{ t('handover.receivedBy') }}</dt>
          <dd>{{ assetRequest.handover.received_by_name }}</dd>
        </div>
        <div>
          <dt>{{ t('handover.handedOutBy') }}</dt>
          <dd>{{ assetRequest.handover.handed_out_by?.display_name ?? '—' }}</dd>
        </div>
        <div
          v-if="
            assetRequest.handover.recorded_by &&
            assetRequest.handover.recorded_by.id !== assetRequest.handover.handed_out_by?.id
          "
        >
          <dt>{{ t('handover.recordedBy') }}</dt>
          <dd>{{ assetRequest.handover.recorded_by.display_name }}</dd>
        </div>
        <div v-if="assetRequest.handover.location">
          <dt>{{ t('handover.deliveredTo') }}</dt>
          <dd>{{ assetRequest.handover.location }}</dd>
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

    <p v-if="assetRequest.handover?.notes" class="notes">{{ assetRequest.handover.notes }}</p>

    <section class="sign">
      <div class="signature">
        <img v-if="assetRequest.handover?.signature" :src="assetRequest.handover.signature" alt="" />
        <div class="line" />
        <span>{{ t('handover.signature') }} · {{ assetRequest.handover?.received_by_name }}</span>
      </div>
    </section>

    <section v-for="r in returns" :key="r.id" class="return">
      <h2>{{ t('requests.returning.title') }}</h2>
      <dl class="facts">
        <div>
          <dt>{{ t('requests.returning.at') }}</dt>
          <dd class="mono">{{ dateTime(r.returned_at) }}</dd>
        </div>
        <div>
          <dt>{{ t('requests.returning.by') }}</dt>
          <dd>{{ r.returned_by?.display_name ?? '—' }}</dd>
        </div>
      </dl>
      <table>
        <thead>
          <tr>
            <th>{{ t('inventory.fields.inventoryNumber') }}</th>
            <th>{{ t('inventory.fields.model') }}</th>
            <th>{{ t('inventory.fields.serialNumber') }}</th>
            <th>{{ t('common.notes') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in r.rows" :key="row.id">
            <td class="mono">{{ row.number }}</td>
            <td>{{ row.model }}</td>
            <td class="mono">{{ row.serial }}</td>
            <td>
              <strong v-if="row.damaged">{{ t('requests.returning.damaged') }}</strong>
              {{ row.note }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="r.notes" class="notes">{{ r.notes }}</p>
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
.return {
  margin-top: 40px;
  padding-top: 18px;
  border-top: 2px solid #0b1220;
  break-inside: avoid;
}
.return h2 {
  margin: 0;
  font-size: 17px;
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
