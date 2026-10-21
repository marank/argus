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
  NRadioButton,
  NRadioGroup,
} from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { licensesApi } from '@/api/inventory'
import { assetModelsApi, suppliersApi } from '@/api/masterdata'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import type { LicenseDetail, LicenseInput } from '@/types/inventory'

const props = defineProps<{ license?: LicenseDetail | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [license: LicenseDetail] }>()

const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

function empty(): LicenseInput {
  return {
    model: null,
    reference: '',
    license_key: '',
    seats: 1,
    assign_to: 'user',
    valid_from: null,
    valid_until: null,
    supplier: null,
    purchase_date: null,
    purchase_price: null,
    notes: '',
  }
}

const form = reactive<LicenseInput>(empty())

watch(show, (visible) => {
  if (!visible) return
  const l = props.license
  Object.assign(
    form,
    l
      ? {
          model: l.model.id,
          reference: l.reference,
          license_key: l.license_key,
          seats: l.seats,
          assign_to: l.assign_to,
          valid_from: l.valid_from,
          valid_until: l.valid_until,
          supplier: l.supplier?.id ?? null,
          purchase_date: l.purchase_date,
          purchase_price: l.purchase_price,
          notes: l.notes,
        }
      : empty(),
  )
})

const dateModel = (key: 'valid_from' | 'valid_until' | 'purchase_date') =>
  computed({
    get: () => fromIsoDate(form[key]),
    set: (value: number | null) => (form[key] = toIsoDate(value)),
  })
const validFrom = dateModel('valid_from')
const validUntil = dateModel('valid_until')
const purchaseDate = dateModel('purchase_date')
const price = computed({
  get: () => (form.purchase_price ? Number(form.purchase_price) : null),
  set: (value: number | null) => (form.purchase_price = value === null ? null : value.toFixed(2)),
})
/** Whom seats go to cannot change once seats are assigned. */
const assignToLocked = computed(() => !!props.license?.seats_used)

async function save() {
  const saved = await run(
    () => (props.license ? licensesApi.update(props.license.id, form) : licensesApi.create(form)),
    t('common.saved'),
  )
  if (saved) {
    emit('saved', saved)
    show.value = false
  }
}
</script>

<template>
  <NDrawer v-model:show="show" :width="560" placement="right">
    <NDrawerContent
      :title="license ? t('inventory.licenses.editLicense') : t('inventory.licenses.newLicense')"
      closable
    >
      <NForm
        class="ar-form"
        label-placement="top"
        size="medium"
        :show-feedback="false"
        @submit.prevent="save"
      >
        <div class="eyebrow">{{ t('inventory.licenses.sectionLicense') }}</div>
        <NGrid :cols="2" :x-gap="12">
          <NFormItemGi :span="2">
            <template #label
              ><FieldLabel :label="t('inventory.licenses.software')" required
            /></template>
            <EntitySelect
              v-model="form.model"
              :fetcher="assetModelsApi.list"
              :params="{ tracking: 'license', is_active: true }"
              :label="(m) => `${m.full_name} · ${m.category.name}`"
              :initial="
                license ? ({ ...license.model, category: license.category } as never) : null
              "
            />
          </NFormItemGi>
          <NFormItemGi :span="2">
            <template #label
              ><FieldLabel
                :label="t('inventory.licenses.reference')"
                :help="t('inventory.licenses.referenceHelp')"
            /></template>
            <NInput v-model:value="form.reference" />
          </NFormItemGi>
          <NFormItemGi :span="2" :label="t('inventory.licenses.licenseKey')">
            <NInput v-model:value="form.license_key" class="mono-input" />
          </NFormItemGi>
          <NFormItemGi>
            <template #label
              ><FieldLabel :label="t('inventory.licenses.seats')" required
            /></template>
            <NInputNumber
              v-model:value="form.seats"
              :min="Math.max(1, license?.seats_used ?? 0)"
              :precision="0"
              style="width: 100%"
            />
          </NFormItemGi>
          <NFormItemGi>
            <template #label
              ><FieldLabel
                :label="t('inventory.licenses.assignTo')"
                :help="t('inventory.licenses.assignToHelp')"
            /></template>
            <NRadioGroup v-model:value="form.assign_to" :disabled="assignToLocked">
              <NRadioButton value="user">{{ enumLabel('licenseAssignTo', 'user') }}</NRadioButton>
              <NRadioButton value="device">{{
                enumLabel('licenseAssignTo', 'device')
              }}</NRadioButton>
            </NRadioGroup>
          </NFormItemGi>
          <NFormItemGi :label="t('inventory.licenses.validFrom')">
            <DateField v-model:value="validFrom" type="date" clearable style="width: 100%" />
          </NFormItemGi>
          <NFormItemGi>
            <template #label
              ><FieldLabel
                :label="t('inventory.licenses.validUntil')"
                :help="t('inventory.licenses.validUntilHelp')"
            /></template>
            <DateField v-model:value="validUntil" type="date" clearable style="width: 100%" />
          </NFormItemGi>
        </NGrid>

        <NDivider />
        <div class="eyebrow">{{ t('inventory.licenses.sectionPurchase') }}</div>
        <NGrid :cols="2" :x-gap="12">
          <NFormItemGi :label="t('inventory.fields.supplier')">
            <EntitySelect
              v-model="form.supplier"
              :fetcher="suppliersApi.list"
              :label="(s) => s.name"
              :initial="license?.supplier as never"
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
