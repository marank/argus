<script setup lang="ts">
import type { Id } from '@/types/common'
import { Pencil, Trash2, UserMinus, UserPlus, Wrench } from '@lucide/vue'
import { NAlert, NButton, NCard, NModal, NSkeleton, useMessage } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { assetsApi, eventsApi } from '@/api/inventory'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import AssetEventModal from '@/components/inventory/AssetEventModal.vue'
import AssetFormDrawer from '@/components/inventory/AssetFormDrawer.vue'
import AssetTimeline from '@/components/inventory/AssetTimeline.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import type { AssetDetail, AssetEvent } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
// Without the right to change assets, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('assets', 'write'))
const features = useFeaturesStore()
const router = useRouter()
const message = useMessage()
const confirm = useConfirm()
const { date, dateTime, money, enumLabel } = useFormat()
const { busy, run } = useAction()

const asset = ref<AssetDetail | null>(null)
const events = ref<AssetEvent[]>([])
const showForm = ref(false)
const showEvent = ref(false)
const showAssign = ref(false)
const assignTo = ref<Id | null>(null)

async function load() {
  ;[asset.value, events.value] = await Promise.all([
    assetsApi.get(props.id),
    assetsApi.events(props.id),
  ])
}
onMounted(load)

const identification = computed<DetailEntry[]>(() => {
  const a = asset.value!
  return [
    { label: t('inventory.fields.serialNumber'), value: a.serial_number, mono: true },
    { label: t('inventory.fields.imei'), value: a.imei, mono: true },
    { label: t('inventory.fields.macAddress'), value: a.mac_address, mono: true },
    { label: t('inventory.fields.hostname'), value: a.hostname, mono: true },
    { label: t('inventory.fields.manufacturer'), value: a.manufacturer.name },
    { label: t('inventory.fields.category'), value: a.category.name },
    { label: t('inventory.fields.parent'), slot: 'parent' },
    { label: t('inventory.fields.components'), slot: 'components' },
  ]
})

const usage = computed<DetailEntry[]>(() => {
  const a = asset.value!
  return [
    { label: t('inventory.fields.condition'), value: enumLabel('condition', a.condition) },
    { label: t('inventory.fields.location'), value: a.location?.full_name },
    { label: t('inventory.fields.assignedTo'), value: a.assigned_to?.display_name },
    {
      label: t('inventory.fields.assignedSince'),
      value: a.assigned_since ? dateTime(a.assigned_since) : null,
      mono: true,
    },
    {
      label: t('inventory.fields.loanable'),
      value: a.is_loanable ? t('common.yes') : t('common.no'),
    },
  ]
})

const purchase = computed<DetailEntry[]>(() => {
  const a = asset.value!
  return [
    { label: t('inventory.fields.supplier'), value: a.supplier?.name },
    { label: t('inventory.fields.purchaseDate'), value: date(a.purchase_date), mono: true },
    { label: t('inventory.fields.purchasePrice'), value: money(a.purchase_price), mono: true },
    { label: t('inventory.fields.warrantyUntil'), value: date(a.warranty_until), mono: true },
    ...(a.notes ? [{ label: t('common.notes'), value: a.notes, wide: true }] : []),
  ]
})

/** Consumables of this device: assigned directly, then those compatible with its model. */
const consumables = computed(() => {
  const a = asset.value!
  const own = a.consumables.map((model) => ({ model, fromModel: false }))
  const ids = new Set(a.consumables.map((m) => m.id))
  const viaModel = a.model_consumables
    .filter((m) => !ids.has(m.id))
    .map((model) => ({ model, fromModel: true }))
  return [...own, ...viaModel]
})

async function assign(user: Id | null) {
  const updated = await run(() => assetsApi.assign(props.id, user), t('common.saved'))
  if (updated) {
    showAssign.value = false
    await load()
  }
}

async function remove() {
  if (!(await confirm(t('common.confirmDelete'), { danger: true }))) return
  if (await run(() => assetsApi.remove(props.id))) {
    message.success(t('common.deleted'))
    router.push({ name: 'assets' })
  }
}

async function removeEvent(event: AssetEvent) {
  if (!(await confirm(t('common.confirmDelete'), { danger: true }))) return
  await run(() => eventsApi.remove(event.id))
  await load()
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!asset" height="240px" />
    <template v-else>
      <PageHeader :title="asset.model.full_name">
        <template #eyebrow>
          <span class="mono id">{{ asset.inventory_number }}</span>
        </template>
        <template #badge>
          <StatusTag group="assetStatus" :value="asset.status" />
        </template>
        <template v-if="canWrite" #actions>
          <NButton v-if="asset.assigned_to" :loading="busy" @click="assign(null)">
            <template #icon><UserMinus :size="15" /></template>
            {{ t('inventory.unassign') }}
          </NButton>
          <NButton v-else-if="asset.status === 'in_stock'" @click="showAssign = true">
            <template #icon><UserPlus :size="15" /></template>
            {{ t('inventory.assign') }}
          </NButton>
          <NButton @click="showEvent = true">
            <template #icon><Wrench :size="15" /></template>
            {{ t('inventory.recordEvent') }}
          </NButton>
          <NButton @click="showForm = true">
            <template #icon><Pencil :size="15" /></template>
            {{ t('common.edit') }}
          </NButton>
          <NButton quaternary type="error" :title="t('common.delete')" @click="remove">
            <template #icon><Trash2 :size="15" /></template>
          </NButton>
        </template>
      </PageHeader>

      <div class="layout">
        <div class="stack">
          <NAlert v-if="asset.reservation" type="info" :bordered="false">
            <RouterLink :to="{ name: 'reservation', params: { id: asset.reservation.id } }">
              {{
                t('inventory.activeReservation', {
                  number: asset.reservation.number,
                  name: asset.reservation.requester.display_name,
                })
              }}
            </RouterLink>
          </NAlert>
          <NAlert
            v-if="features.isOn('issues') && asset.open_issues.length"
            type="warning"
            :bordered="false"
          >
            <RouterLink :to="{ name: 'issues' }">
              {{
                t(
                  'inventory.issues.openOnDevice',
                  { count: asset.open_issues.length },
                  asset.open_issues.length,
                )
              }}:
            </RouterLink>
            {{
              asset.open_issues
                .map((i) => `${enumLabel('issueKind', i.kind)} – ${i.description}`)
                .join(' · ')
            }}
          </NAlert>
          <NCard size="small">
            <div class="hero">
              <span class="icon"
                ><component :is="categoryIcon(asset.category.icon)" :size="26" :stroke-width="1.4"
              /></span>
              <DetailGrid :entries="identification">
                <template #parent>
                  <RouterLink
                    v-if="asset.parent"
                    :to="{ name: 'asset', params: { id: asset.parent.id } }"
                    class="mono"
                    >{{ asset.parent.inventory_number }}</RouterLink
                  >
                  <span v-else>—</span>
                </template>
                <template #components>
                  <span v-if="!asset.components.length">—</span>
                  <RouterLink
                    v-for="c in asset.components"
                    :key="c.id"
                    :to="{ name: 'asset', params: { id: c.id } }"
                    class="mono comp"
                    >{{ c.inventory_number }}</RouterLink
                  >
                </template>
              </DetailGrid>
            </div>
          </NCard>
          <NCard :title="t('inventory.sections.usage')" size="small"
            ><DetailGrid :entries="usage"
          /></NCard>
          <NCard
            v-if="features.isOn('consumables')"
            :title="t('inventory.fields.consumables')"
            size="small"
          >
            <div v-if="consumables.length" class="consumables">
              <span v-for="c in consumables" :key="c.model.id" class="consumable">
                {{ c.model.full_name }}
                <span v-if="c.fromModel" class="muted small">{{ t('inventory.viaModel') }}</span>
              </span>
            </div>
            <span v-else class="muted">{{ t('inventory.noConsumables') }}</span>
          </NCard>
          <NCard
            v-if="features.isOn('licenses')"
            :title="t('inventory.licenses.deviceLicenses')"
            size="small"
          >
            <div v-if="asset.licenses.length" class="consumables">
              <RouterLink
                v-for="l in asset.licenses"
                :key="l.id"
                :to="{ name: 'license', params: { id: l.id } }"
                class="consumable"
              >
                {{ l.model.full_name }}
                <span v-if="l.valid_until" class="muted small mono">{{ date(l.valid_until) }}</span>
              </RouterLink>
            </div>
            <span v-else class="muted">{{ t('inventory.licenses.noDeviceLicenses') }}</span>
          </NCard>
          <NCard :title="t('inventory.sections.purchase')" size="small"
            ><DetailGrid :entries="purchase"
          /></NCard>
        </div>
        <NCard :title="t('inventory.history')" size="small" class="history">
          <AssetTimeline :events="events" @remove="removeEvent" />
        </NCard>
      </div>

      <AssetFormDrawer v-model:show="showForm" :asset="asset" @saved="load" />
      <AssetEventModal v-model:show="showEvent" :asset-id="asset.id" @saved="load" />
      <NModal
        v-model:show="showAssign"
        preset="card"
        :title="t('inventory.assignTo')"
        style="max-width: 420px"
      >
        <EntitySelect
          v-model="assignTo"
          :fetcher="usersApi.list"
          :params="{ is_active: true }"
          :label="(u) => u.display_name"
        />
        <template #footer>
          <div class="row" style="justify-content: flex-end">
            <NButton @click="showAssign = false">{{ t('common.cancel') }}</NButton>
            <NButton
              type="primary"
              :disabled="!assignTo"
              :loading="busy"
              @click="assign(assignTo)"
              >{{ t('inventory.assign') }}</NButton
            >
          </div>
        </template>
      </NModal>
    </template>
  </div>
</template>

<style scoped>
.id {
  font-size: 12px;
  color: var(--ar-primary);
  letter-spacing: 0.02em;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 1fr);
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
.comp {
  margin-right: 8px;
}
.consumables {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.consumable {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 3px 10px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  font-size: 12.5px;
}
.small {
  font-size: 11px;
}
@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
