<script setup lang="ts">
import {
  NButton,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NSelect,
} from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi, suppliersApi } from '@/api/masterdata'
import { loadComponentTypes } from '@/utils/components'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import FormSection from '@/components/common/FormSection.vue'
import ToggleRow from '@/components/common/ToggleRow.vue'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { useFieldErrors } from '@/composables/useFieldErrors'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import { useFeaturesStore } from '@/stores/features'
import { modelLabel } from '@/utils/models'
import type { Id } from '@/types/common'
import { ASSET_CONDITIONS, ASSET_STATUSES } from '@/types/inventory'

const props = defineProps<{ asset?: Schemas['AssetDetailOut'] | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [asset: Schemas['AssetDetailOut']] }>()

const { t } = useI18n()
const features = useFeaturesStore()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

/** The model stays empty until one is picked; saving waits for it. */
type Form = Omit<Schemas['AssetIn'], 'model'> & { model: Id | null }

function empty(): Form {
  return {
    model: null,
    inventory_number: '',
    serial_number: '',
    identifier: '',
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
    consumables: [],
    installed_components: null,
    notes: '',
  }
}

const form = reactive<Form>(empty())
const fieldErrors = useFieldErrors(form)

watch(show, (visible) => {
  if (!visible) return
  fieldErrors.clear()
  const a = props.asset
  Object.assign(
    form,
    a
      ? {
          model: a.model.id,
          inventory_number: a.inventory_number,
          serial_number: a.serial_number,
          identifier: a.identifier,
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
          consumables: a.consumables.map((c) => c.id),
          installed_components: null,
          notes: a.notes,
        }
      : empty(),
  )
  category.value = a?.category ?? null
  parts.value = Object.fromEntries(
    (a?.installed_components ?? []).map((c) => [
      c.component_type.id,
      { serial_number: c.serial_number, installed_on: fromIsoDate(c.installed_on) },
    ]),
  )
  fillParts()
})

/** The category of the chosen model: names the identifier and brings the tracked parts. */
const category = ref<Schemas['CategoryRefOut'] | null>(null)
const identifierLabel = computed(() =>
  category.value?.identifier_label
    ? `${t('inventory.fields.identifier')} (${category.value.identifier_label})`
    : t('inventory.fields.identifier'),
)
/** The tracked parts of devices of this category, e.g. the battery. */
const componentTypes = ref<Schemas['ComponentTypeOut'][]>([])
/** Serial number and date of each part, by component type. */
const parts = ref<Record<Id, { serial_number: string; installed_on: number | null }>>({})
watch(
  () => category.value?.id,
  async (id) => {
    componentTypes.value = await loadComponentTypes(id)
    fillParts()
  },
)
/** An empty entry for each part not recorded yet. */
function fillParts() {
  for (const type of componentTypes.value)
    parts.value[type.id] ??= { serial_number: '', installed_on: null }
}

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
  const data = {
    ...form,
    model: form.model!,
    installed_components: componentTypes.value.map((type) => ({
      component_type: type.id,
      serial_number: parts.value[type.id]?.serial_number ?? '',
      installed_on: toIsoDate(parts.value[type.id]?.installed_on ?? null),
    })),
  }
  const saved = await run(
    () =>
      (props.asset ? assetsApi.update(props.asset.id, data) : assetsApi.create(data)).catch(
        fieldErrors.capture,
      ),
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
        size="medium"
        :show-feedback="false"
        @submit.prevent="save"
      >
        <FormSection :title="t('inventory.sections.identification')">
          <NGrid :cols="2" :x-gap="12">
            <NFormItemGi v-bind="fieldErrors.item('model')" :span="2">
              <template #label
                ><FieldLabel :label="t('inventory.fields.model')" required
              /></template>
              <EntitySelect
                v-model="form.model"
                :fetcher="assetModelsApi.list"
                :params="{ tracking: 'serialized', is_active: true }"
                :label="(m) => `${modelLabel(m)} · ${m.category.name}`"
                :initial="asset ? ({ ...asset.model, category: asset.category } as never) : null"
                @select="(m) => (category = m?.category ?? null)"
              />
            </NFormItemGi>
            <NFormItemGi v-bind="fieldErrors.item('inventory_number')">
              <template #label
                ><FieldLabel
                  :label="t('inventory.fields.inventoryNumber')"
                  :help="asset ? undefined : t('inventory.fields.inventoryNumberHint')"
              /></template>
              <NInput v-model:value="form.inventory_number" class="mono-input" placeholder="auto" />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('serial_number')"
              :label="t('inventory.fields.serialNumber')"
            >
              <NInput v-model:value="form.serial_number" class="mono-input" />
            </NFormItemGi>
            <NFormItemGi v-bind="fieldErrors.item('identifier')">
              <template #label
                ><FieldLabel :label="identifierLabel" :help="t('inventory.fields.identifierHelp')"
              /></template>
              <NInput v-model:value="form.identifier" class="mono-input" />
            </NFormItemGi>
            <NFormItemGi v-bind="fieldErrors.item('imei')" :label="t('inventory.fields.imei')">
              <NInput v-model:value="form.imei" class="mono-input" />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('mac_address')"
              :label="t('inventory.fields.macAddress')"
            >
              <NInput
                v-model:value="form.mac_address"
                class="mono-input"
                placeholder="00:00:00:00:00:00"
              />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('hostname')"
              :label="t('inventory.fields.hostname')"
            >
              <NInput v-model:value="form.hostname" class="mono-input" />
            </NFormItemGi>
            <NFormItemGi v-bind="fieldErrors.item('parent')" :label="t('inventory.fields.parent')">
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
        </FormSection>

        <FormSection v-if="componentTypes.length" :title="t('inventory.sections.components')">
          <NGrid :cols="2" :x-gap="12">
            <template v-for="type in componentTypes" :key="type.id">
              <NFormItemGi
                v-if="parts[type.id]"
                v-bind="fieldErrors.item('installed_components')"
                :label="t('inventory.fields.partSerial', { part: type.name })"
              >
                <NInput v-model:value="parts[type.id]!.serial_number" class="mono-input" />
              </NFormItemGi>
              <NFormItemGi v-if="parts[type.id]" :label="t('inventory.fields.installedOn')">
                <DateField
                  v-model:value="parts[type.id]!.installed_on"
                  type="date"
                  clearable
                  style="width: 100%"
                />
              </NFormItemGi>
            </template>
          </NGrid>
        </FormSection>

        <FormSection :title="t('inventory.sections.usage')">
          <NGrid :cols="2" :x-gap="12">
            <NFormItemGi v-bind="fieldErrors.item('status')" :label="t('common.status')">
              <NSelect v-model:value="form.status" :options="statusOptions" />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('condition')"
              :label="t('inventory.fields.condition')"
            >
              <NSelect v-model:value="form.condition" :options="conditionOptions" />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('location')"
              :label="t('inventory.fields.location')"
            >
              <EntitySelect
                v-model="form.location"
                :fetcher="locationsApi.list"
                :label="(l) => l.full_name"
                :initial="asset?.location as never"
              />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('assigned_to')"
              :label="t('inventory.fields.assignedTo')"
            >
              <EntitySelect
                v-model="form.assigned_to"
                :fetcher="usersApi.list"
                :label="(u) => u.display_name"
                :initial="asset?.assigned_to as never"
              />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('consumables')"
              v-if="features.isOn('consumables')"
              :span="2"
            >
              <template #label
                ><FieldLabel
                  :label="t('inventory.fields.consumables')"
                  :help="t('inventory.fields.consumablesHelp')"
              /></template>
              <EntitySelect
                v-model="form.consumables"
                multiple
                :fetcher="assetModelsApi.list"
                :params="{ tracking: 'bulk', is_active: true }"
                :label="modelLabel"
                :initial="asset?.consumables as never"
              />
            </NFormItemGi>
          </NGrid>
          <div class="toggles">
            <ToggleRow
              v-model="form.is_loanable"
              :label="t('inventory.fields.loanable')"
              :help="t('inventory.fields.loanableHelp')"
              :error="fieldErrors.errors.is_loanable"
            />
          </div>
        </FormSection>

        <FormSection :title="t('inventory.sections.purchase')">
          <NGrid :cols="2" :x-gap="12">
            <NFormItemGi
              v-bind="fieldErrors.item('supplier')"
              :label="t('inventory.fields.supplier')"
            >
              <EntitySelect
                v-model="form.supplier"
                :fetcher="suppliersApi.list"
                :label="(s) => s.name"
                :initial="asset?.supplier as never"
              />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('purchase_price')"
              :label="t('inventory.fields.purchasePrice')"
            >
              <NInputNumber v-model:value="price" :precision="2" :min="0" style="width: 100%">
                <template #suffix>€</template>
              </NInputNumber>
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('purchase_date')"
              :label="t('inventory.fields.purchaseDate')"
            >
              <DateField v-model:value="purchaseDate" type="date" clearable style="width: 100%" />
            </NFormItemGi>
            <NFormItemGi
              v-bind="fieldErrors.item('warranty_until')"
              :label="t('inventory.fields.warrantyUntil')"
            >
              <DateField v-model:value="warrantyUntil" type="date" clearable style="width: 100%" />
            </NFormItemGi>
            <NFormItemGi v-bind="fieldErrors.item('notes')" :span="2" :label="t('common.notes')">
              <NInput
                v-model:value="form.notes"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 6 }"
              />
            </NFormItemGi>
          </NGrid>
        </FormSection>
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
.toggles {
  margin-top: 6px;
  border-top: 1px solid var(--ar-border);
}
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
</style>
