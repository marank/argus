<script setup lang="ts">
import {
  NButton,
  NDivider,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NSelect,
} from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi, suppliersApi } from '@/api/masterdata'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import {
  ASSET_CONDITIONS,
  ASSET_STATUSES,
  type AssetDetail,
  type AssetInput,
} from '@/types/inventory'

const props = defineProps<{ asset?: AssetDetail | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [asset: AssetDetail] }>()

const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

function empty(): AssetInput {
  return {
    model: null,
    inventory_number: '',
    serial_number: '',
    imei: '',
    mac_address: '',
    hostname: '',
    status: 'in_stock',
    condition: 'new',
    is_loanable: true,
    location: null,
    assigned_to: null,
    parent: null,
    supplier: null,
    purchase_date: null,
    purchase_price: null,
    warranty_until: null,
    notes: '',
  }
}

const form = reactive<AssetInput>(empty())

watch(show, (visible) => {
  if (!visible) return
  const a = props.asset
  Object.assign(
    form,
    a
      ? {
          model: a.model.id,
          inventory_number: a.inventory_number,
          serial_number: a.serial_number,
          imei: a.imei,
          mac_address: a.mac_address,
          hostname: a.hostname,
          status: a.status,
          condition: a.condition,
          is_loanable: a.is_loanable,
          location: a.location?.id ?? null,
          assigned_to: a.assigned_to?.id ?? null,
          parent: a.parent?.id ?? null,
          supplier: a.supplier?.id ?? null,
          purchase_date: a.purchase_date,
          purchase_price: a.purchase_price,
          warranty_until: a.warranty_until,
          notes: a.notes,
        }
      : empty(),
  )
})

const statusOptions = computed(() =>
  ASSET_STATUSES.map((s) => ({ value: s, label: enumLabel('assetStatus', s) })),
)
const conditionOptions = computed(() =>
  ASSET_CONDITIONS.map((c) => ({ value: c, label: enumLabel('condition', c) })),
)

const dateModel = (key: 'purchase_date' | 'warranty_until') =>
  computed({
    get: () => fromIsoDate(form[key]),
    set: (value: number | null) => (form[key] = toIsoDate(value)),
  })
const purchaseDate = dateModel('purchase_date')
const warrantyUntil = dateModel('warranty_until')
const price = computed({
  get: () => (form.purchase_price ? Number(form.purchase_price) : null),
  set: (value: number | null) => (form.purchase_price = value === null ? null : value.toFixed(2)),
})

async function save() {
  const saved = await run(
    () => (props.asset ? assetsApi.update(props.asset.id, form) : assetsApi.create(form)),
    t('common.saved'),
  )
  if (saved) {
    emit('saved', saved)
    show.value = false
  }
}
</script>

<template>
  <NDrawer v-model:show="show" :width="620" placement="right">
    <NDrawerContent
      :title="
        asset ? `${t('inventory.editAsset')} · ${asset.inventory_number}` : t('inventory.newAsset')
      "
      closable
    >
      <NForm
        class="ar-form"
        label-placement="top"
        size="small"
        :show-feedback="false"
        @submit.prevent="save"
      >
        <div class="eyebrow">{{ t('inventory.sections.identification') }}</div>
        <NGrid :cols="2" :x-gap="12">
          <NFormItemGi :span="2">
            <template #label><FieldLabel :label="t('inventory.fields.model')" required /></template>
            <EntitySelect
              v-model="form.model"
              :fetcher="assetModelsApi.list"
              :params="{ tracking: 'serialized', is_active: true }"
              :label="(m) => `${m.full_name} · ${m.category.name}`"
              :initial="asset ? ({ ...asset.model, category: asset.category } as never) : null"
            />
          </NFormItemGi>
          <NFormItemGi>
            <template #label
              ><FieldLabel
                :label="t('inventory.fields.inventoryNumber')"
                :help="asset ? undefined : t('inventory.fields.inventoryNumberHint')"
            /></template>
            <NInput v-model:value="form.inventory_number" class="mono-input" placeholder="auto" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.serialNumber')">
            <NInput v-model:value="form.serial_number" class="mono-input" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.imei')">
            <NInput v-model:value="form.imei" class="mono-input" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.macAddress')">
            <NInput
              v-model:value="form.mac_address"
              class="mono-input"
              placeholder="00:00:00:00:00:00"
            />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.hostname')">
            <NInput v-model:value="form.hostname" class="mono-input" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.parent')">
            <EntitySelect
              v-model="form.parent"
              :fetcher="assetsApi.list"
              :label="(a) => `${a.inventory_number} · ${a.model.full_name}`"
              :initial="
                asset?.parent ? ({ ...asset.parent, model: { full_name: '' } } as never) : null
              "
            />
          </NFormItemGi>
        </NGrid>

        <NDivider />
        <div class="eyebrow">{{ t('inventory.sections.usage') }}</div>
        <NGrid :cols="2" :x-gap="12">
          <NFormItemGi :label="t('common.status')">
            <NSelect v-model:value="form.status" :options="statusOptions" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.condition')">
            <NSelect v-model:value="form.condition" :options="conditionOptions" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.location')">
            <EntitySelect
              v-model="form.location"
              :fetcher="locationsApi.list"
              :label="(l) => l.full_name"
              :initial="asset?.location as never"
            />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.assignedTo')">
            <EntitySelect
              v-model="form.assigned_to"
              :fetcher="usersApi.list"
              :label="(u) => u.display_name"
              :initial="asset?.assigned_to as never"
            />
          </NFormItemGi>
          <NFormItemGi :show-label="false" style="align-self: end">
            <CheckField
              v-model="form.is_loanable"
              :label="t('inventory.fields.loanable')"
              :help="t('inventory.fields.loanableHelp')"
            />
          </NFormItemGi>
        </NGrid>

        <NDivider />
        <div class="eyebrow">{{ t('inventory.sections.purchase') }}</div>
        <NGrid :cols="2" :x-gap="12">
          <NFormItemGi :label="t('inventory.fields.supplier')">
            <EntitySelect
              v-model="form.supplier"
              :fetcher="suppliersApi.list"
              :label="(s) => s.name"
              :initial="asset?.supplier as never"
            />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.purchasePrice')">
            <NInputNumber v-model:value="price" :precision="2" :min="0" style="width: 100%">
              <template #suffix>€</template>
            </NInputNumber>
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.purchaseDate')">
            <DateField v-model:value="purchaseDate" type="date" clearable style="width: 100%" />
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.fields.warrantyUntil')">
            <DateField v-model:value="warrantyUntil" type="date" clearable style="width: 100%" />
          </NFormItemGi>
          <NFormItemGi :span="2" :label="t('common.notes')">
            <NInput
              v-model:value="form.notes"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 6 }"
            />
          </NFormItemGi>
        </NGrid>
      </NForm>
      <template #footer>
        <div class="row">
          <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="busy" :disabled="!form.model" @click="save">{{
            t('common.save')
          }}</NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.eyebrow {
  margin-bottom: 8px;
}
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
</style>
