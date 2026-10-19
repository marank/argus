<script setup lang="ts">
import { Pencil, Plus, Trash2, X } from '@lucide/vue'
import { NAlert, NButton, NCard, NInput, NSkeleton, NTag } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { assetsApi, licensesApi } from '@/api/inventory'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LicenseFormDrawer from '@/components/inventory/LicenseFormDrawer.vue'
import SeatUsage from '@/components/inventory/SeatUsage.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { LicenseAssignment, LicenseDetail } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const router = useRouter()
const confirm = useConfirm()
const { date, money, enumLabel } = useFormat()
const { busy, run } = useAction()

const license = ref<LicenseDetail | null>(null)
const showForm = ref(false)
const target = ref<Id | null>(null)
const note = ref('')

async function load() {
  license.value = await licensesApi.get(props.id)
}
onMounted(load)

const perDevice = computed(() => license.value?.assign_to === 'device')
const full = computed(() => !!license.value && license.value.seats_used >= license.value.seats)

const details = computed<DetailEntry[]>(() => {
  const l = license.value!
  return [
    { label: t('inventory.licenses.licenseKey'), value: l.license_key, mono: true, wide: true },
    { label: t('inventory.licenses.seats'), slot: 'seats' },
    { label: t('inventory.licenses.assignTo'), value: enumLabel('licenseAssignTo', l.assign_to) },
    { label: t('inventory.licenses.validFrom'), value: date(l.valid_from), mono: true },
    {
      label: t('inventory.licenses.validUntil'),
      value: l.valid_until ? date(l.valid_until) : t('inventory.licenses.perpetual'),
      mono: !!l.valid_until,
    },
    { label: t('inventory.fields.supplier'), value: l.supplier?.name },
    { label: t('inventory.fields.purchaseDate'), value: date(l.purchase_date), mono: true },
    { label: t('inventory.fields.purchasePrice'), value: money(l.purchase_price), mono: true },
    ...(l.notes ? [{ label: t('common.notes'), value: l.notes, wide: true }] : []),
  ]
})

function assigneeName(a: LicenseAssignment): string {
  return a.user?.display_name ?? `${a.asset?.inventory_number} · ${a.asset?.model.full_name}`
}

async function assign() {
  if (!target.value || !license.value) return
  const data = perDevice.value
    ? { asset: target.value, note: note.value }
    : { user: target.value, note: note.value }
  const updated = await run(() => licensesApi.assign(license.value!.id, data), t('common.saved'))
  if (updated) {
    license.value = updated
    target.value = null
    note.value = ''
  }
}

async function unassign(a: LicenseAssignment) {
  if (!(await confirm(t('inventory.licenses.confirmUnassign', { name: assigneeName(a) })))) return
  const updated = await run(() => licensesApi.unassign(license.value!.id, a.id))
  if (updated) license.value = updated
}

async function remove() {
  if (!license.value) return
  if (
    !(await confirm(`${license.value.model.full_name}: ${t('common.confirmDelete')}`, {
      danger: true,
    }))
  )
    return
  if ((await run(() => licensesApi.remove(license.value!.id), t('common.deleted'))) !== undefined)
    router.push({ name: 'licenses' })
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!license" height="320px" />
    <template v-else>
      <PageHeader :title="license.model.full_name" :subtitle="license.reference || undefined">
        <template #eyebrow>
          <span class="eyebrow-line">
            <component :is="categoryIcon(license.category.icon)" :size="13" />
            {{ license.category.name }}
            <NTag v-if="license.is_expired" size="small" type="error" :bordered="false">{{
              t('inventory.licenses.expired')
            }}</NTag>
          </span>
        </template>
        <template #actions>
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
        <NCard size="small">
          <DetailGrid :entries="details">
            <template #seats>
              <SeatUsage :used="license.seats_used" :seats="license.seats" />
            </template>
          </DetailGrid>
        </NCard>

        <NCard :title="t('inventory.licenses.assignments')" size="small">
          <NAlert v-if="full" type="warning" :bordered="false" class="gap">
            {{ t('inventory.licenses.noSeatsLeft') }}
          </NAlert>
          <div v-else-if="!license.is_expired" class="assign">
            <EntitySelect
              v-if="perDevice"
              v-model="target"
              :fetcher="assetsApi.list"
              :label="(a) => `${a.inventory_number} · ${a.model.full_name}`"
              :placeholder="t('inventory.licenses.assignDevice')"
              class="grow"
            />
            <EntitySelect
              v-else
              v-model="target"
              :fetcher="usersApi.list"
              :params="{ is_active: true }"
              :label="(u) => u.display_name"
              :placeholder="t('inventory.licenses.assignUser')"
              class="grow"
            />
            <NInput
              v-model:value="note"
              :placeholder="t('inventory.licenses.note')"
              style="width: 180px"
            />
            <NButton type="primary" :disabled="!target" :loading="busy" @click="assign">
              <template #icon><Plus :size="15" /></template>
              {{ t('common.add') }}
            </NButton>
          </div>

          <p v-if="!license.assignments.length" class="muted">
            {{ t('inventory.licenses.noAssignments') }}
          </p>
          <ul v-else class="assignments">
            <li v-for="a in license.assignments" :key="a.id">
              <div class="who">
                <RouterLink v-if="a.asset" :to="{ name: 'asset', params: { id: a.asset.id } }">
                  <span class="mono">{{ a.asset.inventory_number }}</span>
                  {{ a.asset.model.full_name }}
                </RouterLink>
                <span v-else>{{ a.user?.display_name }}</span>
                <small class="muted">
                  {{ t('inventory.licenses.assignedAt') }} {{ date(a.created_at) }}
                  <template v-if="a.asset?.assigned_to">
                    · {{ a.asset.assigned_to.display_name }}</template
                  >
                  <template v-if="a.note"> · {{ a.note }}</template>
                </small>
              </div>
              <NButton
                quaternary
                size="tiny"
                :title="t('inventory.licenses.unassign')"
                @click="unassign(a)"
              >
                <template #icon><X :size="14" /></template>
              </NButton>
            </li>
          </ul>
        </NCard>
      </div>

      <LicenseFormDrawer v-model:show="showForm" :license="license" @saved="load" />
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
.eyebrow-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.assign {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.grow {
  flex: 1;
  min-width: 0;
}
.gap {
  margin-bottom: 12px;
}
.assignments {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}
.assignments li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--ar-border);
}
.assignments li:last-child {
  border-bottom: none;
}
.who {
  display: grid;
  flex: 1;
  min-width: 0;
}
.who .mono {
  margin-right: 6px;
}
@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .assign {
    flex-wrap: wrap;
  }
}
</style>
