<script setup lang="ts">
import type { Id } from '@/types/common'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
} from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { consumablesApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'

type Direction = 'in' | 'out' | 'adjust'

const props = defineProps<{ item: Schemas['ConsumableOut'] | null; direction: Direction }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const form = reactive({
  direction: 'in' as Direction,
  quantity: 1,
  note: '',
  recipient: null as Id | null,
})

// "Adjust" starts from the current count; booking in/out starts from one unit.
const defaultQuantity = (direction: Direction) =>
  direction === 'adjust' ? (props.item?.quantity ?? 0) : 1

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    direction: props.direction,
    quantity: defaultQuantity(props.direction),
    note: '',
    recipient: null,
  })
})

watch(
  () => form.direction,
  (direction) => (form.quantity = defaultQuantity(direction)),
)

const REASONS: Record<Direction, Schemas['Reason']> = {
  in: 'receipt',
  out: 'issue',
  adjust: 'adjustment',
}
const delta = computed(() => {
  if (form.direction === 'adjust') return form.quantity - (props.item?.quantity ?? 0)
  return form.direction === 'in' ? form.quantity : -form.quantity
})

async function save() {
  if (!props.item) return
  const ok = await run(
    () =>
      consumablesApi.move(props.item!.id, {
        delta: delta.value,
        reason: REASONS[form.direction],
        note: form.note,
        recipient: form.recipient,
      }),
    t('common.saved'),
  )
  if (ok) {
    show.value = false
    emit('saved')
  }
}
</script>

<template>
  <NModal v-model:show="show" preset="card" :title="item?.model.full_name" style="max-width: 460px">
    <p class="muted mono">
      {{ item?.location.full_name }} · {{ t('inventory.consumables.onHand') }}: {{ item?.quantity }}
    </p>
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <NFormItem>
        <NRadioGroup v-model:value="form.direction">
          <NRadioButton value="in">{{ t('inventory.consumables.bookIn') }}</NRadioButton>
          <NRadioButton value="out">{{ t('inventory.consumables.bookOut') }}</NRadioButton>
          <NRadioButton value="adjust">{{ t('inventory.consumables.adjust') }}</NRadioButton>
        </NRadioGroup>
      </NFormItem>
      <NFormItem>
        <template #label>
          <FieldLabel
            :label="
              form.direction === 'adjust' ? t('inventory.consumables.onHand') : t('common.quantity')
            "
          >
            <template #extra>{{
              `${t('inventory.consumables.delta')}: ${delta > 0 ? '+' : ''}${delta}`
            }}</template>
          </FieldLabel>
        </template>
        <NInputNumber
          v-model:value="form.quantity"
          :min="form.direction === 'adjust' ? 0 : 1"
          style="width: 100%"
        />
      </NFormItem>
      <NFormItem v-if="form.direction === 'out'" :label="t('inventory.consumables.recipient')">
        <EntitySelect
          v-model="form.recipient"
          :fetcher="usersApi.list"
          :label="(u) => u.display_name"
        />
      </NFormItem>
      <NFormItem :label="t('common.notes')">
        <NInput v-model:value="form.note" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="delta === 0" @click="save">{{
          t('common.save')
        }}</NButton>
      </div>
    </template>
  </NModal>
</template>
