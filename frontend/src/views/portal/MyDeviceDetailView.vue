<script setup lang="ts">
import { MessageSquareWarning } from '@lucide/vue'
import { NButton, NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { portalApi } from '@/api/requests'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ReportIssueModal from '@/components/portal/ReportIssueModal.vue'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { MyAsset } from '@/types/requests'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'

/** One of the employee's devices with all its problem reports and IT's answers. */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const features = useFeaturesStore()
const { date, dateTime, enumLabel } = useFormat()

const asset = ref<MyAsset | null>(null)
const showReport = ref(false)

async function load() {
  asset.value = await portalApi.myAsset(props.id)
}
onMounted(load)

const details = computed<DetailEntry[]>(() => {
  const a = asset.value!
  return [
    { label: t('inventory.fields.inventoryNumber'), value: a.inventory_number, mono: true },
    { label: t('inventory.fields.serialNumber'), value: a.serial_number, mono: true },
    { label: t('inventory.fields.category'), value: a.category },
    { label: t('inventory.fields.assignedSince'), value: date(a.assigned_since), mono: true },
    {
      label: t('requests.myDevices.returnBy'),
      value: a.return_due
        ? `${date(a.return_due)} · ${a.asset_request_number}`
        : t('common.permanent'),
      mono: !!a.return_due,
    },
  ]
})
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!asset" height="240px" />
    <template v-else>
      <PageHeader :title="asset.model.full_name" :eyebrow="t('requests.myDevices.title')">
        <template #actions>
          <NButton v-if="features.isOn('issues')" type="primary" @click="showReport = true">
            <template #icon><MessageSquareWarning :size="16" /></template>
            {{ t('requests.myDevices.report') }}
          </NButton>
        </template>
      </PageHeader>

      <div class="layout">
        <NCard size="small">
          <div class="hero">
            <span class="icon"
              ><component :is="categoryIcon(asset.category_icon)" :size="26" :stroke-width="1.4"
            /></span>
            <DetailGrid :entries="details" />
          </div>
        </NCard>

        <NCard
          v-if="features.isOn('issues')"
          :title="t('requests.myDevices.reports')"
          size="small"
        >
          <p v-if="!asset.issues.length" class="muted">
            {{ t('requests.myDevices.noReports') }}
          </p>
          <ul v-else class="issues">
            <li v-for="issue in asset.issues" :key="issue.id">
              <!-- Opens the conversation; IT's updates pulse until then. -->
              <RouterLink :to="{ name: 'portal-issue', params: { id: issue.id } }" class="issue">
                <div class="issue-head">
                  <StatusTag
                    group="issueStatus"
                    :value="issue.status"
                    :pulse="issue.unseen_update"
                  />
                  <strong class="small">{{ enumLabel('issueKind', issue.kind) }}</strong>
                  <span class="mono muted small">{{ dateTime(issue.created_at) }}</span>
                </div>
                <p class="text">{{ issue.description }}</p>
                <p
                  v-if="issue.last_message && issue.last_message !== issue.description"
                  class="answer"
                >
                  <span class="eyebrow">{{ t('requests.myDevices.lastMessage') }}</span>
                  {{ issue.last_message }}
                </p>
              </RouterLink>
            </li>
          </ul>
        </NCard>
      </div>

      <ReportIssueModal v-model:show="showReport" :asset="asset" @reported="load" />
    </template>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 18px;
}
.icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.issues {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.issues li {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
.issue {
  display: block;
  color: inherit;
  text-decoration: none;
}
.issue:hover .text {
  color: var(--ar-text);
}
.issue-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.issue-head .mono {
  margin-left: auto;
}
.small {
  font-size: 12px;
}
.text,
.answer {
  margin: 0;
  white-space: pre-wrap;
}
.answer {
  display: grid;
  gap: 2px;
  padding-top: 6px;
  border-top: 1px dashed var(--ar-border);
}
@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
