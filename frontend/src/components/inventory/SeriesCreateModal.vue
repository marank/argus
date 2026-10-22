<script setup lang="ts">
import { watchDebounced } from '@vueuse/core'
import {
  NButton,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  useMessage,
} from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi, suppliersApi } from '@/api/masterdata'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import FormSection from '@/components/common/FormSection.vue'
import ToggleRow from '@/components/common/ToggleRow.vue'
import { useAction } from '@/composables/useAction'
import { useFieldErrors } from '@/composables/useFieldErrors'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import { ASSET_CONDITIONS, type AssetSeriesInput, type AssetSeriesPreview } from '@/types/inventory'
import type { AssetModel } from '@/types/masterdata'
import { modelLabel } from '@/utils/models'

/** Create many identical devices at once; the number sequence of the model or its category numbers them. */
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ created: [] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()
const message = useMessage()

const MAX_COUNT = 500

function empty(): AssetSeriesInput {
  return {
    model: null,
    count: 10,
    condition: 'new',
    is_loanable: true,
    location: null,
    supplier: null,
    purchase_date: null,
    purchase_price: null,
    warranty_until: null,
    notes: '',
  }
}

const form = reactive<AssetSeriesInput>(empty())
const fieldErrors = useFieldErrors(form)
const model = ref<AssetModel | null>(null)
const preview = ref<AssetSeriesPreview | null>(null)
const previewError = ref('')

watch(show, (visible) => {
  if (!visible) return
  fieldErrors.clear()
  Object.assign(form, empty())
  model.value = null
})

/** The model's purchase defaults; whatever was filled in by hand stays. */
function onModel(selected: AssetModel | null) {
  model.value = selected
  if (!selected) return
  form.supplier ??= selected.default_supplier?.id ?? null
  form.purchase_price ??= selected.list_price
  fillWarranty()
}

function fillWarranty() {
  const months = model.value?.warranty_months
  if (!form.purchase_date || !months) return
  const until = new Date(`${form.purchase_date}T00:00:00`)
  until.setMonth(until.getMonth() + months)
  form.warranty_until = toIsoDate(until)
}

watchDebounced(
  () => [form.model, form.count],
  async () => {
    preview.value = null
    previewError.value = ''
    if (!form.model || !form.count) return
    try {
      preview.value = await assetsApi.seriesPreview(form.model, form.count)
    } catch (e) {
      previewError.value = e instanceof Error ? e.message : String(e)
    }
  },
  { debounce: 250 },
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
watch(() => form.purchase_date, fillWarranty)
const price = computed({
  get: () => (form.purchase_price ? Number(form.purchase_price) : null),
  set: (value: number | null) => (form.purchase_price = value === null ? null : value.toFixed(2)),
})

const canSubmit = computed(() => Boolean(form.model && form.count && preview.value))

async function submit() {
  const created = await run(() => assetsApi.createSeries(form).catch(fieldErrors.capture))
  if (created) {
    show.value = false
    emit('created')
    message.success(
      t('inventory.series.created', {
        count: created.length,
        first: preview.value?.first,
        last: preview.value?.last,
      }),
    )
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('inventory.series.title')"
    style="max-width: 680px"
  >
    <p class="muted intro">{{ t('inventory.series.help') }}</p>
    <NForm
      class="ar-form"
      label-placement="top"
      size="medium"
      :show-feedback="false"
      @submit.prevent="submit"
    >
      <FormSection :title="t('inventory.series.section')">
        <NGrid :cols="4" :x-gap="12">
          <NFormItemGi v-bind="fieldErrors.item('model')" :span="3">
            <template #label><FieldLabel :label="t('inventory.fields.model')" required /></template>
            <EntitySelect
              v-model="form.model"
              :fetcher="assetModelsApi.list"
              :params="{ tracking: 'serialized', is_active: true, numbered: true }"
              :label="(m) => `${modelLabel(m)} · ${m.category.name}`"
              @select="onModel"
            />
          </NFormItemGi>
          <NFormItemGi v-bind="fieldErrors.item('count')">
            <template #label><FieldLabel :label="t('inventory.series.count')" required /></template>
            <NInputNumber
              v-model:value="form.count"
              :min="1"
              :max="MAX_COUNT"
              :precision="0"
              style="width: 100%"
            />
          </NFormItemGi>
        </NGrid>
        <div class="numbers" :class="{ invalid: previewError }">
          <span class="eyebrow">{{ t('inventory.series.numbers') }}</span>
          <span v-if="previewError" class="error">{{ previewError }}</span>
          <span v-else-if="preview" class="range">
            <code class="mono">{{ preview.first }}</code>
            <template v-if="preview.last !== preview.first">
              <span class="muted">–</span>
              <code class="mono">{{ preview.last }}</code>
            </template>
            <span class="muted sequence">{{ preview.sequence }}</span>
          </span>
          <span v-else class="muted">{{ t('inventory.series.pickModel') }}</span>
        </div>
      </FormSection>

      <FormSection :title="t('inventory.sections.usage')">
        <NGrid :cols="2" :x-gap="12">
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
              :initial="model?.default_supplier as never"
            />
          </NFormItemGi>
          <NFormItemGi v-bind="fieldErrors.item('purchase_price')">
            <template #label
              ><FieldLabel
                :label="t('inventory.fields.purchasePrice')"
                :help="t('inventory.series.priceHelp')"
            /></template>
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
          <NFormItemGi v-bind="fieldErrors.item('warranty_until')">
            <template #label
              ><FieldLabel
                :label="t('inventory.fields.warrantyUntil')"
                :help="t('inventory.series.warrantyHelp')"
            /></template>
            <DateField v-model:value="warrantyUntil" type="date" clearable style="width: 100%" />
          </NFormItemGi>
          <NFormItemGi v-bind="fieldErrors.item('notes')" :span="2" :label="t('common.notes')">
            <NInput
              v-model:value="form.notes"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 5 }"
            />
          </NFormItemGi>
        </NGrid>
      </FormSection>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :disabled="!canSubmit" :loading="busy" @click="submit">
          {{ t('inventory.series.submit', { count: form.count ?? 0 }) }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.intro {
  margin: 0 0 12px;
}
.numbers {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 14px;
  margin-top: 12px;
  padding: 10px 12px;
  border: 1px dashed var(--ar-border-strong);
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
.range {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
code {
  padding: 1px 6px;
  border-radius: 2px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-weight: 600;
}
.sequence {
  font-size: 12px;
}
.invalid {
  border-color: var(--ar-error);
}
.error {
  color: var(--ar-error);
  font-size: 12px;
}
.toggles {
  margin-top: 6px;
  border-top: 1px solid var(--ar-border);
}
</style>
