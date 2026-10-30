<script setup lang="ts">
import { NDataTable, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { approvalsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'

/** Requests of the approver's departments waiting for a decision, oldest first. */
const { t } = useI18n()
const router = useRouter()
const { date } = useFormat()

const requests = ref<Schemas['AssetRequestListOut'][] | null>(null)

async function load() {
  requests.value = (await approvalsApi.list({ page_size: 100 })).items
}
onMounted(load)
useLive(['request'], load)

const period = (r: Schemas['AssetRequestListOut']) =>
  `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : t('common.permanent')}`

const columns = computed<DataTableColumns<Schemas['AssetRequestListOut']>>(() => [
  {
    key: 'number',
    title: t('requests.number'),
    width: 120,
    render: (r) => h('span', { class: 'mono' }, r.number),
  },
  {
    key: 'requester',
    title: t('requests.requester'),
    minWidth: 180,
    render: (r) =>
      h('div', [
        h('div', r.requester.display_name),
        r.department ? h('small', { class: 'muted' }, r.department.name) : null,
      ]),
  },
  {
    key: 'title',
    title: t('requests.purpose'),
    minWidth: 240,
    render: (r) => h('div', [h('div', r.title), h('small', { class: 'muted' }, r.summary)]),
  },
  {
    key: 'period',
    title: t('requests.period'),
    width: 200,
    render: (r) => h('span', { class: 'mono' }, period(r)),
  },
  {
    key: 'created_at',
    title: t('common.createdAt'),
    width: 120,
    render: (r) => h('span', { class: 'mono' }, date(r.created_at)),
  },
])
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('requests.approvals.title')"
      :subtitle="t('requests.approvals.subtitle')"
    />
    <EmptyState v-if="requests && !requests.length" :text="t('requests.approvals.empty')" />
    <NDataTable
      v-else
      class="clickable-rows"
      size="small"
      :columns="columns"
      :data="requests ?? []"
      :loading="!requests"
      :row-key="(r: Schemas['AssetRequestListOut']) => r.id"
      :row-props="
        (r: Schemas['AssetRequestListOut']) => ({
          onClick: () => router.push({ name: 'portal-approval', params: { id: r.id } }),
        })
      "
      :scroll-x="1000"
    />
  </div>
</template>
