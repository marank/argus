<script setup lang="ts">
import { useLive } from '@/composables/useLive'
import type { Id } from '@/types/common'
import { RotateCcw, X } from '@lucide/vue'
import { NAlert, NButton, NCard, NDataTable, NSkeleton, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import HandoverCard from '@/components/requests/HandoverCard.vue'
import RequestSteps from '@/components/requests/RequestSteps.vue'
import OriginTag from '@/components/requests/OriginTag.vue'
import ReturnsCard from '@/components/requests/ReturnsCard.vue'
import ApprovalCard from '@/components/requests/detail/ApprovalCard.vue'
import HandoverPlanCard from '@/components/requests/detail/HandoverPlanCard.vue'
import RequestInfoCard from '@/components/requests/detail/RequestInfoCard.vue'
import RequestHistory from '@/components/requests/detail/RequestHistory.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { allocationCode, allocationModel, handoverPlanned, itemLabel } from '@/utils/requests'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const route = useRoute()
const confirm = useConfirm()
const { busy, run } = useAction()

const assetRequest = ref<Schemas['AssetRequestOut'] | null>(null)

const load = async () => (assetRequest.value = await requestsApi.get(props.id))
onMounted(load)
useLive(['request'], load, { id: () => props.id })

/** Lent for a period: when it is due back, then what came back. */
/** Coming from the new request page (`?created=1`) and still waiting: say it went in. */
const justSubmitted = computed(
  () =>
    !!route.query.created &&
    (assetRequest.value?.status === 'submitted' ||
      assetRequest.value?.status === 'pending_approval'),
)

const showReturns = computed(() => {
  const r = assetRequest.value
  if (!r) return false
  return (
    r.returns.length > 0 ||
    (r.duration === 'temporary' && ['handed_out', 'completed'].includes(r.status) && !!r.handover)
  )
})

async function cancel() {
  if (!(await confirm(t('requests.actions.confirmCancel'), { danger: true }))) return
  const updated = await run(() => requestsApi.cancel(props.id))
  if (updated) assetRequest.value = updated
}

const columns: DataTableColumns<Schemas['AssetRequestItemOut']> = [
  {
    key: 'label',
    title: () => t('requests.items'),
    render: (i) =>
      h('div', [h('div', itemLabel(i)), i.note ? h('small', { class: 'muted' }, i.note) : null]),
  },
  {
    key: 'requested',
    title: () => t('requests.quantities.requested'),
    width: 120,
    align: 'right',
    render: (i) => h('span', { class: 'mono' }, i.quantity_requested),
  },
  {
    key: 'confirmed',
    title: () => t('requests.quantities.confirmed'),
    width: 120,
    align: 'right',
    render: (i) =>
      h(
        'span',
        {
          class: [
            'mono',
            i.quantity_confirmed !== null && i.quantity_confirmed < i.quantity_requested
              ? 'reduced'
              : '',
          ],
        },
        i.quantity_confirmed ?? '—',
      ),
  },
  {
    key: 'devices',
    title: () => t('inventory.fields.inventoryNumber'),
    render: (i) =>
      h(
        'span',
        { class: 'mono muted' },
        i.allocations.map((a) => allocationCode(a) || allocationModel(a)).join(', ') || '—',
      ),
  },
]
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!assetRequest" height="200px" />
    <template v-else>
      <PageHeader :title="assetRequest.title" :eyebrow="assetRequest.number">
        <template #badge
          ><StatusTag
            group="requestStatus"
            :value="assetRequest.status"
            :pulse="assetRequest.status === 'ready'" /><OriginTag :origin="assetRequest.origin"
        /></template>
        <template #actions>
          <NButton
            v-if="
              ['pending_approval', 'submitted', 'confirmed', 'ready'].includes(assetRequest.status)
            "
            :loading="busy"
            @click="cancel"
          >
            <template #icon><X :size="15" /></template>
            {{ t('requests.actions.cancel') }}
          </NButton>
          <RouterLink
            v-if="['rejected', 'cancelled', 'completed'].includes(assetRequest.status)"
            :to="{ name: 'portal-new', query: { from: assetRequest.id } }"
          >
            <NButton :type="assetRequest.status === 'completed' ? 'default' : 'primary'">
              <template #icon><RotateCcw :size="15" /></template>
              {{ t('requests.again.action') }}
            </NButton>
          </RouterLink>
        </template>
      </PageHeader>

      <div class="stack">
        <NAlert v-if="justSubmitted" type="success" :bordered="false">
          {{
            t(
              assetRequest.status === 'pending_approval'
                ? 'requests.new.submittedForApproval'
                : 'requests.new.submitted',
              { number: assetRequest.number },
            )
          }}
        </NAlert>
        <NCard size="small"><RequestSteps :assetRequest="assetRequest" /></NCard>
        <div class="layout">
          <div class="stack">
            <NCard :title="t('requests.items')" size="small">
              <NDataTable
                size="small"
                :columns="columns"
                :data="assetRequest.items"
                :bordered="false"
              />
            </NCard>
            <RequestHistory :assetRequest="assetRequest" />
          </div>
          <!-- First on narrow screens: how and when the devices come matters most. -->
          <div class="stack side">
            <HandoverCard
              v-if="assetRequest.handover"
              :assetRequest="assetRequest"
              :printable="false"
            />
            <HandoverPlanCard
              v-else-if="
                ['confirmed', 'ready'].includes(assetRequest.status) &&
                handoverPlanned(assetRequest)
              "
              :assetRequest="assetRequest"
              for-employee
            />
            <ReturnsCard
              v-if="showReturns"
              :assetRequest="assetRequest"
              with-due
              :printable="false"
            />
            <RequestInfoCard :assetRequest="assetRequest" />
            <ApprovalCard v-if="assetRequest.approval" :assetRequest="assetRequest" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(300px, 1fr);
  gap: 16px;
  align-items: start;
}
@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 1100px) {
  .side {
    order: -1;
  }
}
:deep(.reduced) {
  color: var(--ar-warning);
  font-weight: 600;
}
</style>
