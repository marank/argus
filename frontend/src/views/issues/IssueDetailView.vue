<script setup lang="ts">
import { NSkeleton } from 'naive-ui'
import { computed, ref, useTemplateRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { issuesApi } from '@/api/inventory'
import { portalApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import IssueConversation from '@/components/issues/IssueConversation.vue'
import IssueDeviceCard from '@/components/issues/IssueDeviceCard.vue'
import IssueReporterCard from '@/components/issues/IssueReporterCard.vue'
import IssueStatusCard from '@/components/issues/IssueStatusCard.vue'
import OtherIssuesCard from '@/components/issues/OtherIssuesCard.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { useAuthStore } from '@/stores/auth'
import { useMenuCountsStore } from '@/stores/menuCounts'
import type { Id } from '@/types/common'

/**
 * A problem report with its conversation, for IT (`viewer` "it") and for the
 * reporter in the self-service portal. Either side writes at any time and marks
 * the problem resolved; only IT takes it into work or reopens it.
 */
const props = defineProps<{ id: Id; viewer: Schemas['IssueEntryOut']['side'] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const auth = useAuthStore()
const menuCounts = useMenuCountsStore()
const { busy, run } = useAction()

const forIt = computed(() => props.viewer === 'it')
const canWrite = computed(() => !forIt.value || auth.can('issues', 'write'))

const issue = ref<Schemas['AssetIssueDetailOut'] | null>(null)
const conversation = useTemplateRef('conversation')

async function refresh() {
  issue.value = forIt.value ? await issuesApi.get(props.id) : await portalApi.myIssue(props.id)
  // Opening the report marks IT's updates seen: the menu stops pulsing.
  if (!forIt.value) void menuCounts.refresh()
}
// Other reports on the device open on the same page.
watch(
  () => props.id,
  () => {
    issue.value = null
    void refresh()
  },
  { immediate: true },
)
// New messages and status changes of the other side appear while the page is open.
useLive(['issue'], refresh, { id: () => props.id })

async function send(text: string) {
  const updated = await run(
    () =>
      forIt.value ? issuesApi.message(props.id, text) : portalApi.myIssueMessage(props.id, text),
    t('inventory.issues.detail.sent'),
  )
  if (updated) {
    issue.value = updated
    conversation.value?.clear()
  }
}

async function changeStatus(status: Schemas['AssetIssueStatus'], text: string) {
  const updated = await run(() =>
    forIt.value
      ? issuesApi.update(props.id, { status, message: text })
      : portalApi.resolveMyIssue(props.id, text),
  )
  if (updated) {
    issue.value = updated
    conversation.value?.clear()
    // A resolved or reopened report changes the open count in the menu.
    void menuCounts.refresh()
  }
}

const assign = computed(() =>
  forIt.value && canWrite.value
    ? (data: { team: Id | null; assignee: Id | null }) => issuesApi.assign(props.id, data)
    : undefined,
)
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!issue" height="200px" />
    <template v-else>
      <PageHeader
        :title="`${enumLabel('issueKind', issue.kind)}: ${issue.asset.model.full_name}`"
        :eyebrow="issue.asset.inventory_number"
      >
        <template #badge>
          <!-- New reports wait for IT. -->
          <StatusTag
            group="issueStatus"
            :value="issue.status"
            :pulse="forIt && issue.status === 'open'"
          />
        </template>
      </PageHeader>

      <div class="layout">
        <IssueConversation
          ref="conversation"
          :issue="issue"
          :viewer="viewer"
          :can-write="canWrite"
          :busy="busy"
          @send="send"
          @status="changeStatus"
        />
        <!-- First on narrow screens: what the report is about. -->
        <div class="stack side">
          <IssueStatusCard :issue="issue" :assign="assign" @updated="issue = $event" />
          <IssueDeviceCard :issue="issue" :viewer="viewer" />
          <IssueReporterCard v-if="forIt && issue.reported_by" :reporter="issue.reported_by" />
          <OtherIssuesCard
            v-if="issue.other_issues.length"
            :issues="issue.other_issues"
            :route="forIt ? 'issue' : 'portal-issue'"
          />
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
  .side {
    order: -1;
  }
}
</style>
