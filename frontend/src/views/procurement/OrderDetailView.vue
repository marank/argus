<script setup lang="ts">
import type { Id } from '@/types/common'
import { PackageCheck, Plus, Save, Send, Trash2, X } from '@lucide/vue'
import {
  NButton,
  NCard,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NSkeleton,
  NTable,
} from 'naive-ui'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { assetModelsApi, locationsApi, suppliersApi } from '@/api/masterdata'
import { ordersApi } from '@/api/procurement'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import DateField from '@/components/common/DateField.vue'
import ReceiveModal from '@/components/procurement/ReceiveModal.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import type { Order, OrderLineInput } from '@/types/procurement'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
// Without the right to change procurement, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('procurement', 'write'))
const router = useRouter()
const confirm = useConfirm()
const { date, money } = useFormat()
const { busy, run } = useAction()

const order = ref<Order | null>(null)
const showReceive = ref(false)
const showOrdered = ref(false)

const header = reactive({
  supplier: null as Id | null,
  expected_date: null as number | null,
  supplier_reference: '',
  delivery_location: null as Id | null,
  notes: '',
})
const lines = ref<(OrderLineInput & { price: number | null })[]>([])
const ordered = reactive({
  order_date: Date.now() as number | null,
  expected_date: null as number | null,
  supplier_reference: '',
})

function apply(value: Order) {
  order.value = value
  Object.assign(header, {
    supplier: value.supplier?.id ?? null,
    expected_date: fromIsoDate(value.expected_date),
    supplier_reference: value.supplier_reference,
    delivery_location: value.delivery_location?.id ?? null,
    notes: value.notes,
  })
  lines.value = value.lines.map((line) => ({
    id: line.id,
    asset_model: line.asset_model?.id ?? null,
    description: line.description,
    quantity: line.quantity,
    unit_price: line.unit_price,
    price: line.unit_price ? Number(line.unit_price) : null,
    reservation_item: line.reservation_item?.id ?? null,
  }))
}

onMounted(async () => apply(await ordersApi.get(props.id)))

const isDraft = computed(() => order.value?.status === 'draft')
const editable = computed(
  () => order.value && !['received', 'cancelled'].includes(order.value.status),
)
const draftTotal = computed(() =>
  lines.value.reduce((sum, l) => sum + (l.price ?? 0) * l.quantity, 0),
)

async function save() {
  const updated = await run(
    () =>
      ordersApi.update(props.id, {
        ...header,
        expected_date: toIsoDate(header.expected_date),
        lines: isDraft.value
          ? lines.value.map(({ price, ...line }) => ({
              ...line,
              unit_price: price === null ? null : price.toFixed(2),
            }))
          : undefined,
      }),
    t('common.saved'),
  )
  if (updated) apply(updated)
}

async function markOrdered() {
  await save()
  const updated = await run(() =>
    ordersApi.markOrdered(props.id, {
      order_date: toIsoDate(ordered.order_date),
      expected_date: toIsoDate(ordered.expected_date),
      supplier_reference: ordered.supplier_reference,
    }),
  )
  if (updated) {
    apply(updated)
    showOrdered.value = false
  }
}

async function cancelOrder() {
  if (!(await confirm(t('procurement.orders.confirmCancel'), { danger: true }))) return
  const updated = await run(() => ordersApi.cancel(props.id))
  if (updated) apply(updated)
}

async function remove() {
  if (!(await confirm(t('common.confirmDelete'), { danger: true }))) return
  if ((await run(() => ordersApi.remove(props.id), t('common.deleted'))) !== undefined)
    router.push({ name: 'orders' })
}

function openOrdered() {
  ordered.expected_date = header.expected_date
  ordered.supplier_reference = header.supplier_reference
  showOrdered.value = true
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!order" height="240px" />
    <template v-else>
      <PageHeader :title="order.supplier?.name ?? t('procurement.orders.new')">
        <template #eyebrow
          ><span class="mono id">{{ order.number }}</span></template
        >
        <template #badge><StatusTag group="orderStatus" :value="order.status" /></template>
        <template v-if="canWrite" #actions>
          <NButton v-if="editable" :loading="busy" @click="save">
            <template #icon><Save :size="15" /></template>
            {{ t('common.save') }}
          </NButton>
          <NButton v-if="isDraft" type="primary" @click="openOrdered">
            <template #icon><Send :size="15" /></template>
            {{ t('procurement.orders.markOrdered') }}
          </NButton>
          <NButton
            v-if="['ordered', 'partially_received'].includes(order.status)"
            type="primary"
            @click="showReceive = true"
          >
            <template #icon><PackageCheck :size="15" /></template>
            {{ t('procurement.orders.receive') }}
          </NButton>
          <NButton
            v-if="['draft', 'ordered'].includes(order.status)"
            quaternary
            @click="cancelOrder"
          >
            <template #icon><X :size="15" /></template>
            {{ t('procurement.orders.cancelOrder') }}
          </NButton>
          <NButton
            v-if="isDraft"
            quaternary
            type="error"
            :title="t('common.delete')"
            @click="remove"
          >
            <template #icon><Trash2 :size="15" /></template>
          </NButton>
        </template>
      </PageHeader>

      <div class="stack">
        <NCard size="small">
          <NForm
            class="ar-form"
            label-placement="top"
            size="small"
            :show-feedback="false"
            :disabled="!editable"
          >
            <NGrid :cols="4" :x-gap="12" responsive="screen" item-responsive>
              <NFormItemGi span="4 m:2 l:1" :label="t('procurement.orders.supplier')">
                <EntitySelect
                  v-model="header.supplier"
                  :fetcher="suppliersApi.list"
                  :label="(s) => s.name"
                  :initial="order.supplier as never"
                  :disabled="!editable"
                />
              </NFormItemGi>
              <NFormItemGi span="4 m:2 l:1" :label="t('procurement.orders.supplierReference')">
                <NInput v-model:value="header.supplier_reference" />
              </NFormItemGi>
              <NFormItemGi span="4 m:2 l:1" :label="t('procurement.orders.expectedDate')">
                <DateField
                  v-model:value="header.expected_date"
                  type="date"
                  clearable
                  style="width: 100%"
                />
              </NFormItemGi>
              <NFormItemGi span="4 m:2 l:1" :label="t('procurement.orders.deliveryLocation')">
                <EntitySelect
                  v-model="header.delivery_location"
                  :fetcher="locationsApi.list"
                  :label="(l) => l.full_name"
                  :initial="order.delivery_location as never"
                  :disabled="!editable"
                />
              </NFormItemGi>
              <NFormItemGi span="4" :label="t('common.notes')">
                <NInput
                  v-model:value="header.notes"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 4 }"
                />
              </NFormItemGi>
            </NGrid>
          </NForm>
          <div class="meta mono muted">
            {{ t('procurement.orders.orderDate') }}: {{ date(order.order_date) }} ·
            {{ t('common.createdAt') }}: {{ date(order.created_at) }}
            <template v-if="order.created_by"> · {{ order.created_by.display_name }}</template>
          </div>
        </NCard>

        <NCard :title="t('procurement.orders.lines')" size="small">
          <template #header-extra
            ><span class="mono"
              >{{ t('common.total') }} {{ money(isDraft ? draftTotal : order.total) }}</span
            ></template
          >
          <NTable size="small" :bordered="false">
            <thead>
              <tr>
                <th>{{ t('procurement.orders.item') }}</th>
                <th style="width: 100px" class="num">{{ t('common.quantity') }}</th>
                <th style="width: 140px" class="num">{{ t('procurement.orders.unitPrice') }}</th>
                <th v-if="!isDraft" style="width: 100px" class="num">
                  {{ t('procurement.orders.received') }}
                </th>
                <th v-if="isDraft" style="width: 40px" />
              </tr>
            </thead>
            <tbody v-if="isDraft">
              <tr v-for="(line, index) in lines" :key="line.id ?? `new${index}`">
                <td>
                  <div class="line-edit">
                    <EntitySelect
                      v-model="line.asset_model"
                      size="small"
                      :fetcher="assetModelsApi.list"
                      :label="(m) => m.full_name"
                      :initial="
                        (order.lines.find((l) => l.id === line.id)?.asset_model ?? null) as never
                      "
                      :placeholder="t('inventory.fields.model')"
                    />
                    <NInput
                      v-model:value="line.description"
                      size="small"
                      :placeholder="t('procurement.orders.description')"
                    />
                  </div>
                  <small
                    v-if="order.lines.find((l) => l.id === line.id)?.reservation_item"
                    class="muted"
                  >
                    {{
                      t('procurement.orders.forReservation', {
                        number: order.lines.find((l) => l.id === line.id)!.reservation_item!
                          .reservation.number,
                      })
                    }}
                  </small>
                </td>
                <td class="num">
                  <NInputNumber v-model:value="line.quantity" size="small" :min="1" />
                </td>
                <td class="num">
                  <NInputNumber v-model:value="line.price" size="small" :min="0" :precision="2"
                    ><template #suffix>€</template></NInputNumber
                  >
                </td>
                <td>
                  <NButton
                    quaternary
                    size="tiny"
                    :disabled="lines.length < 2"
                    @click="lines.splice(index, 1)"
                  >
                    <template #icon><Trash2 :size="13" /></template>
                  </NButton>
                </td>
              </tr>
              <tr>
                <td colspan="4">
                  <NButton
                    size="small"
                    dashed
                    @click="
                      lines.push({
                        asset_model: null,
                        description: '',
                        quantity: 1,
                        unit_price: null,
                        price: null,
                      })
                    "
                  >
                    <template #icon><Plus :size="14" /></template>
                    {{ t('procurement.orders.addLine') }}
                  </NButton>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr v-for="line in order.lines" :key="line.id">
                <td>
                  {{ line.label }}
                  <RouterLink
                    v-if="line.reservation_item"
                    :to="{
                      name: 'reservation',
                      params: { id: line.reservation_item.reservation.id },
                    }"
                    class="mono small"
                  >
                    {{
                      t('procurement.orders.forReservation', {
                        number: line.reservation_item.reservation.number,
                      })
                    }}
                  </RouterLink>
                </td>
                <td class="num mono">{{ line.quantity }}</td>
                <td class="num mono">{{ money(line.unit_price) }}</td>
                <td class="num mono" :class="{ done: line.quantity_open === 0 }">
                  {{ line.quantity_received }}
                </td>
              </tr>
            </tbody>
          </NTable>
        </NCard>
      </div>

      <ReceiveModal v-model:show="showReceive" :order="order" @saved="apply" />
      <NModal
        v-model:show="showOrdered"
        preset="card"
        :title="t('procurement.orders.markOrdered')"
        style="max-width: 440px"
      >
        <NForm class="ar-form" label-placement="top" size="small" :show-feedback="false">
          <NGrid :cols="2" :x-gap="12">
            <NFormItemGi :label="t('procurement.orders.orderDate')">
              <DateField v-model:value="ordered.order_date" type="date" style="width: 100%" />
            </NFormItemGi>
            <NFormItemGi :label="t('procurement.orders.expectedDate')">
              <DateField
                v-model:value="ordered.expected_date"
                type="date"
                clearable
                style="width: 100%"
              />
            </NFormItemGi>
            <NFormItemGi :span="2" :label="t('procurement.orders.supplierReference')">
              <NInput v-model:value="ordered.supplier_reference" />
            </NFormItemGi>
          </NGrid>
        </NForm>
        <template #footer>
          <div class="row" style="justify-content: flex-end">
            <NButton @click="showOrdered = false">{{ t('common.cancel') }}</NButton>
            <NButton type="primary" :loading="busy" @click="markOrdered">{{
              t('procurement.orders.markOrdered')
            }}</NButton>
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
}
.num {
  text-align: right;
}
.small {
  margin-left: 8px;
  font-size: 11.5px;
}
.line-edit {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.done {
  color: var(--ar-success);
  font-weight: 600;
}
.meta {
  margin-top: 4px;
  font-size: 11.5px;
}
</style>
