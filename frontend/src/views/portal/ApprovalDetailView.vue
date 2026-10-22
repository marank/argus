<script setup lang="ts">
import { useLive } from '@/composables/useLive'
import type { Id } from '@/types/common'
import { ArrowLeft, Check, X } from '@lucide/vue'
import { NAlert, NButton, NInput, NModal, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { approvalsApi, requestsApi } from '@/api/requests'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ApprovalCard from '@/components/requests/detail/ApprovalCard.vue'
import RequestInfoCard from '@/components/requests/detail/RequestInfoCard.vue'
import RequestedItems from '@/components/requests/detail/RequestedItems.vue'
import RequestHistory from '@/components/requests/detail/RequestHistory.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { AssetRequest } from '@/types/requests'

/**
 * A request as its department's approver sees it: what is asked for, by whom, and
 * the decision. What IT does afterwards is not the approver's business.
 */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const router = useRouter()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const assetRequest = ref<AssetRequest | null>(null)
const load = async () => (assetRequest.value = await requestsApi.get(props.id))
onMounted(load)

// The kind stays while the dialog fades out, so its texts do not switch on closing.
const decision = ref<'approve' | 'decline'>('approve')
const deciding = ref(false)
const comment = ref('')
useLive(['request'], load, { id: () => props.id, paused: () => deciding.value })

/** Why the earlier request ended: the department's or IT's comment. */
const earlierReason = computed(() => {
  const f = assetRequest.value?.follows
  if (!f) return ''
  return f.approval === 'rejected' ? f.approval_comment : f.it_comment
})

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
    t(approve ? 'requests.approvals.approved' : 'requests.approvals.declined'),
  )
  if (updated) {
    // Decided: done for the approver, back to what still waits.
    deciding.value = false
    router.push({ name: 'portal-approvals' })
  }
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!assetRequest" height="200px" />
    <template v-else>
      <PageHeader :title="assetRequest.title" :eyebrow="assetRequest.number">
        <template #badge><StatusTag group="approval" :value="assetRequest.approval" /></template>
        <template #actions>
          <RouterLink :to="{ name: 'portal-approvals' }">
            <NButton quaternary>
              <template #icon><ArrowLeft :size="15" /></template>
              {{ t('requests.approvals.back') }}
            </NButton>
          </RouterLink>
          <template v-if="assetRequest.can_approve">
            <NButton @click="open('decline')">
              <template #icon><X :size="15" /></template>
              {{ t('requests.approvals.decline') }}
            </NButton>
            <NButton type="primary" @click="open('approve')">
              <template #icon><Check :size="15" /></template>
              {{ t('requests.approvals.approve') }}
            </NButton>
          </template>
        </template>
      </PageHeader>

      <div class="stack">
        <NAlert
          v-if="assetRequest.follows"
          type="warning"
          :title="t('requests.again.approverTitle', { number: assetRequest.follows.number })"
        >
          {{ enumLabel('requestStatus', assetRequest.follows.status) }}
          <template v-if="earlierReason">: „{{ earlierReason }}“</template>
        </NAlert>
        <div class="layout">
          <div class="stack">
            <RequestedItems :assetRequest="assetRequest" />
            <RequestInfoCard :assetRequest="assetRequest" />
          </div>
          <div class="stack">
            <ApprovalCard :assetRequest="assetRequest" />
            <RequestHistory :assetRequest="assetRequest" />
          </div>
        </div>
      </div>

      <NModal
        v-model:show="deciding"
        preset="card"
        :title="
          t(
            decision === 'approve'
              ? 'requests.approvals.approveTitle'
              : 'requests.approvals.declineTitle',
          )
        "
        style="max-width: 460px"
      >
        <p v-if="decision === 'approve'" class="muted hint">
          {{ t('requests.approvals.approveHint') }}
        </p>
        <NInput
          v-model:value="comment"
          type="textarea"
          :placeholder="
            t(
              decision === 'approve'
                ? 'requests.approvals.comment'
                : 'requests.approvals.declineReason',
            )
          "
          :autosize="{ minRows: 3 }"
        />
        <template #footer>
          <div class="row" style="justify-content: flex-end">
            <NButton @click="deciding = false">{{ t('common.cancel') }}</NButton>
            <NButton v-if="decision === 'approve'" type="primary" :loading="busy" @click="decide">{{
              t('requests.approvals.approve')
            }}</NButton>
            <NButton
              v-else
              type="error"
              :disabled="!comment.trim()"
              :loading="busy"
              @click="decide"
              >{{ t('requests.approvals.decline') }}</NButton
            >
          </div>
        </template>
      </NModal>
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
.hint {
  margin: 0 0 10px;
}
</style>
