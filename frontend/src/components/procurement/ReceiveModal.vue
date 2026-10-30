<script setup lang="ts">
import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { ordersApi, type ReceiptInput } from '@/api/procurement'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'

interface ReceiptDraft {
  line: Schemas['PurchaseOrderLineOut']
  quantity: number
  serials: string
}

const props = defineProps<{ order: Schemas['PurchaseOrderOut'] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [order: Schemas['PurchaseOrderOut']] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const location = ref<Id | null>(null)
const receipts = ref<ReceiptDraft[]>([])

const parseSerials = (text: string) =>
  text
    .split(/[\n,;\t]+/)
    .map((s) => s.trim())
    .filter(Boolean)

watch(show, (visible) => {
  if (!visible) return
  location.value = props.order.delivery_location?.id ?? null
  receipts.value = props.order.lines
    .filter((line) => line.quantity_open > 0 && line.asset_model)
    .map((line) => ({ line, quantity: line.quantity_open, serials: '' }))
})

async function save() {
  const payload: ReceiptInput[] = receipts.value
    .map((r) => {
      const serials = r.line.asset_model?.tracking === 'serialized' ? parseSerials(r.serials) : []
      return {
        line: r.line.id,
        quantity: serials.length || r.quantity,
        serial_numbers: serials,
        location: location.value,
      }
    })
    .filter((r) => r.quantity > 0)
  const order = await run(() => ordersApi.receive(props.order.id, payload), t('common.saved'))
  if (order) {
    show.value = false
    emit('saved', order)
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="`${t('procurement.orders.receive')} · ${order.number}`"
    style="max-width: 720px"
  >
    <p class="muted">{{ t('procurement.orders.receiveHint') }}</p>
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <NFormItem :label="t('procurement.orders.deliveryLocation')">
        <EntitySelect
          v-model="location"
          :fetcher="locationsApi.list"
          :label="(l) => l.full_name"
          :initial="order.delivery_location as never"
        />
      </NFormItem>
      <div v-for="receipt in receipts" :key="receipt.line.id" class="receipt">
        <div class="head">
          <strong>{{ receipt.line.label }}</strong>
          <span class="mono muted"
            >{{ t('procurement.orders.open') }}: {{ receipt.line.quantity_open }}</span
          >
        </div>
        <NFormItem v-if="receipt.line.asset_model?.tracking === 'serialized'">
          <template #label>
            <FieldLabel :label="t('procurement.orders.serials')">
              <template #extra>{{
                t('inventory.bulk.count', { count: parseSerials(receipt.serials).length })
              }}</template>
            </FieldLabel>
          </template>
          <NInput
            v-model:value="receipt.serials"
            type="textarea"
            class="serials"
            :autosize="{ minRows: 3, maxRows: 10 }"
          />
        </NFormItem>
        <NFormItem
          v-if="
            receipt.line.asset_model?.tracking !== 'serialized' ||
            !parseSerials(receipt.serials).length
          "
          :label="t('common.quantity')"
        >
          <NInputNumber
            v-model:value="receipt.quantity"
            :min="0"
            :max="receipt.line.quantity_open"
            style="width: 140px"
          />
        </NFormItem>
      </div>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">{{
          t('procurement.orders.receive')
        }}</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.receipt {
  padding: 10px 0;
  border-top: 1px solid var(--ar-border);
}
.head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.serials :deep(textarea) {
  font-family: var(--ar-font-mono);
  font-size: 12px;
}
</style>
