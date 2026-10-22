<script setup lang="ts">
import type { Id } from '@/types/common'
import { modelLabel } from '@/utils/models'
import { Trash2 } from '@lucide/vue'
import { NButton, NForm, NFormItem, NInputNumber, NModal, NTable, useMessage } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { assetModelsApi, suppliersApi } from '@/api/masterdata'
import { ordersApi } from '@/api/procurement'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'

export interface DraftLine {
  label: string
  asset_model: Id | null
  quantity: number
  asset_request_item?: Id | null
  /** Restrict model choice to a category when the request was "any of category". */
  category?: Id | null
}

/** Turn demand (request items or low stock) into a purchase order draft. */
const props = defineProps<{ lines: DraftLine[]; supplier?: Id | null }>()
const show = defineModel<boolean>('show', { required: true })
const { t } = useI18n()
const router = useRouter()
const message = useMessage()
const { busy, run } = useAction()

const draft = ref<DraftLine[]>([])
const supplierId = ref<Id | null>(null)

watch(show, (visible) => {
  if (!visible) return
  draft.value = props.lines.map((line) => ({ ...line }))
  supplierId.value = props.supplier ?? null
})

async function create() {
  const order = await run(() =>
    ordersApi.create({
      supplier: supplierId.value,
      expected_date: null,
      supplier_reference: '',
      delivery_location: null,
      notes: '',
      lines: draft.value.map((line) => ({
        asset_model: line.asset_model,
        description: line.asset_model ? '' : line.label,
        quantity: line.quantity,
        unit_price: null,
        asset_request_item: line.asset_request_item ?? null,
      })),
    }),
  )
  if (order) {
    message.success(t('procurement.orders.created', { number: order.number }))
    show.value = false
    router.push({ name: 'order', params: { id: order.id } })
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('procurement.needs.createOrder')"
    style="max-width: 760px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <NFormItem :label="t('procurement.orders.supplier')">
        <EntitySelect
          v-model="supplierId"
          :fetcher="suppliersApi.list"
          :params="{ is_active: true }"
          :label="(s) => s.name"
        />
      </NFormItem>
      <NTable size="small" :bordered="false">
        <thead>
          <tr>
            <th>{{ t('procurement.orders.item') }}</th>
            <th style="width: 280px">{{ t('inventory.fields.model') }}</th>
            <th style="width: 110px">{{ t('common.quantity') }}</th>
            <th style="width: 40px" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="(line, index) in draft" :key="index">
            <td>{{ line.label }}</td>
            <td>
              <EntitySelect
                v-model="line.asset_model"
                size="small"
                :fetcher="assetModelsApi.list"
                :params="line.category ? { category: line.category } : {}"
                :label="modelLabel"
              />
            </td>
            <td><NInputNumber v-model:value="line.quantity" size="small" :min="1" /></td>
            <td>
              <NButton quaternary size="tiny" @click="draft.splice(index, 1)">
                <template #icon><Trash2 :size="13" /></template>
              </NButton>
            </td>
          </tr>
        </tbody>
      </NTable>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="!draft.length" @click="create">{{
          t('procurement.needs.createOrder')
        }}</NButton>
      </div>
    </template>
  </NModal>
</template>
