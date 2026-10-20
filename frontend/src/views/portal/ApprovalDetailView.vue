<script setup lang="ts">
import type { Id } from '@/types/common'
import { ArrowLeft, Check, X } from '@lucide/vue'
import {
  NButton,
  NCard,
  NDataTable,
  NInput,
  NModal,
  NSkeleton,
  type DataTableColumns,
} from 'naive-ui'
import { h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { approvalsApi, reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ReservationInfo from '@/components/reservations/ReservationInfo.vue'
import ReservationSteps from '@/components/reservations/ReservationSteps.vue'
import { useAction } from '@/composables/useAction'
import type { Reservation, ReservationItem } from '@/types/reservations'
import { itemLabel } from '@/utils/reservations'

/** A request as its department's approver sees it, with the decision to take. */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const { busy, run } = useAction()

const reservation = ref<Reservation | null>(null)
onMounted(async () => (reservation.value = await reservationsApi.get(props.id)))

// The kind stays while the dialog fades out, so its texts do not switch on closing.
const decision = ref<'approve' | 'decline'>('approve')
const deciding = ref(false)
const comment = ref('')

function open(kind: 'approve' | 'decline') {
  comment.value = ''
  decision.value = kind
  deciding.value = true
}

async function decide() {
  const approve = decision.value === 'approve'
  const updated = await run(
    () =>
      approve
        ? approvalsApi.approve(props.id, comment.value)
        : approvalsApi.decline(props.id, comment.value),
    t(approve ? 'reservations.approvals.approved' : 'reservations.approvals.declined'),
  )
  if (updated) {
    reservation.value = updated
    deciding.value = false
  }
}

const columns: DataTableColumns<ReservationItem> = [
  {
    key: 'label',
    title: () => t('reservations.items'),
    render: (i) =>
      h('div', [h('div', itemLabel(i)), i.note ? h('small', { class: 'muted' }, i.note) : null]),
  },
  {
    key: 'requested',
    title: () => t('reservations.quantities.requested'),
    width: 120,
    align: 'right',
    render: (i) => h('span', { class: 'mono' }, i.quantity_requested),
  },
]
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!reservation" height="200px" />
    <template v-else>
      <PageHeader :title="reservation.title" :eyebrow="reservation.number">
        <template #badge
          ><StatusTag group="reservationStatus" :value="reservation.status"
        /></template>
        <template #actions>
          <RouterLink :to="{ name: 'portal-approvals' }">
            <NButton quaternary>
              <template #icon><ArrowLeft :size="15" /></template>
              {{ t('reservations.approvals.back') }}
            </NButton>
          </RouterLink>
          <template v-if="reservation.can_approve">
            <NButton @click="open('decline')">
              <template #icon><X :size="15" /></template>
              {{ t('reservations.approvals.decline') }}
            </NButton>
            <NButton type="primary" @click="open('approve')">
              <template #icon><Check :size="15" /></template>
              {{ t('reservations.approvals.approve') }}
            </NButton>
          </template>
        </template>
      </PageHeader>

      <div class="stack">
        <NCard size="small"><ReservationSteps :reservation="reservation" /></NCard>
        <NCard size="small"><ReservationInfo :reservation="reservation" /></NCard>
        <NCard :title="t('reservations.items')" size="small">
          <NDataTable size="small" :columns="columns" :data="reservation.items" :bordered="false" />
        </NCard>
      </div>

      <NModal
        v-model:show="deciding"
        preset="card"
        :title="
          t(
            decision === 'approve'
              ? 'reservations.approvals.approveTitle'
              : 'reservations.approvals.declineTitle',
          )
        "
        style="max-width: 460px"
      >
        <p v-if="decision === 'approve'" class="muted hint">
          {{ t('reservations.approvals.approveHint') }}
        </p>
        <NInput
          v-model:value="comment"
          type="textarea"
          :placeholder="
            t(
              decision === 'approve'
                ? 'reservations.approvals.comment'
                : 'reservations.approvals.declineReason',
            )
          "
          :autosize="{ minRows: 3 }"
        />
        <template #footer>
          <div class="row" style="justify-content: flex-end">
            <NButton @click="deciding = false">{{ t('common.cancel') }}</NButton>
            <NButton v-if="decision === 'approve'" type="primary" :loading="busy" @click="decide">{{
              t('reservations.approvals.approve')
            }}</NButton>
            <NButton
              v-else
              type="error"
              :disabled="!comment.trim()"
              :loading="busy"
              @click="decide"
              >{{ t('reservations.approvals.decline') }}</NButton
            >
          </div>
        </template>
      </NModal>
    </template>
  </div>
</template>

<style scoped>
.hint {
  margin: 0 0 10px;
}
</style>
