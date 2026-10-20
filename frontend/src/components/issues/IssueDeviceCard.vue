<script setup lang="ts">
import { ArrowUpRight } from '@lucide/vue'
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RouteLocationRaw } from 'vue-router'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { AssetIssueDetail, IssueSide } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'

/**
 * The device the report is about. IT also sees where it is, when it was bought
 * and the hostname; the reporter what helps them describe it.
 */
const props = defineProps<{ issue: AssetIssueDetail; viewer: IssueSide }>()
const { t } = useI18n()
const { date } = useFormat()

const asset = computed(() => props.issue.asset)
const forIt = computed(() => props.viewer === 'it')

const warrantyOver = computed(
  () => !!asset.value.warranty_until && new Date(asset.value.warranty_until) < new Date(),
)

/** IT opens the device record; the reporter their device page while they still have it. */
const link = computed<RouteLocationRaw | null>(() => {
  if (forIt.value) return { name: 'asset', params: { id: asset.value.id } }
  return props.issue.still_assigned
    ? { name: 'portal-device', params: { id: asset.value.id } }
    : null
})

const entries = computed<DetailEntry[]>(() => {
  const a = asset.value
  return [
    { label: t('inventory.issues.detail.category'), value: a.category },
    { label: t('inventory.issues.detail.serialNumber'), value: a.serial_number, mono: true },
    ...(forIt.value && a.hostname
      ? [{ label: t('inventory.issues.detail.hostname'), value: a.hostname, mono: true }]
      : []),
    ...(forIt.value
      ? [
          { label: t('common.status'), slot: 'status' },
          { label: t('inventory.issues.detail.location'), value: a.location?.full_name },
          { label: t('inventory.issues.detail.assignedTo'), slot: 'assigned', wide: true },
          {
            label: t('inventory.issues.detail.purchaseDate'),
            value: date(a.purchase_date),
            mono: true,
          },
        ]
      : []),
    { label: t('inventory.issues.detail.warranty'), slot: 'warranty' },
  ]
})
</script>

<template>
  <NCard :title="t('inventory.issues.detail.device')" size="small">
    <template v-if="link" #header-extra>
      <RouterLink :to="link" class="open-link small">
        {{ t('inventory.issues.detail.openDevice') }} <ArrowUpRight :size="13" />
      </RouterLink>
    </template>
    <div class="stack">
      <div class="device">
        <span class="icon"><component :is="categoryIcon(asset.category_icon)" :size="20" /></span>
        <div>
          <div class="model">{{ asset.model.full_name }}</div>
          <div class="mono muted small">{{ asset.inventory_number }}</div>
        </div>
      </div>
      <p v-if="!forIt && !issue.still_assigned" class="muted small returned">
        {{ t('inventory.issues.detail.returned') }}
      </p>
      <DetailGrid :entries="entries">
        <template #status>
          <StatusTag group="assetStatus" :value="asset.status" />
        </template>
        <template #assigned>
          <template v-if="asset.assigned_to">
            {{ asset.assigned_to.display_name }}
            <span v-if="asset.assigned_since" class="muted small">
              · {{ t('inventory.issues.detail.since', { date: date(asset.assigned_since) }) }}
            </span>
          </template>
          <span v-else class="muted">{{ t('inventory.issues.detail.notAssigned') }}</span>
        </template>
        <template #warranty>
          <span class="mono">{{ asset.warranty_until ? date(asset.warranty_until) : '—' }}</span>
          <span v-if="warrantyOver" class="over small">
            · {{ t('inventory.issues.detail.warrantyOver') }}</span
          >
        </template>
      </DetailGrid>
    </div>
  </NCard>
</template>

<style scoped>
.device {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid var(--ar-border);
  background: var(--ar-surface-sunken);
  color: var(--ar-text-muted);
}
.model {
  font-weight: 600;
}
.returned {
  margin: 0;
}
.over {
  color: var(--ar-warning);
  font-weight: 600;
}
.open-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
</style>
