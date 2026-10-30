<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NCheckbox, NForm, NFormItem, NInput, NModal } from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import { useAction } from '@/composables/useAction'
import { allocationCode, allocationModel, isReturnable } from '@/utils/requests'

/** Take back some or all lent devices and seats, with a note per device and a record. */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const form = reactive({
  selected: [] as Id[],
  damaged: [] as Id[],
  notes: '',
  allocationNotes: {} as Record<Id, string>,
})

/** Still with the employee: handed out, not yet back. */
const open = computed(() =>
  props.assetRequest.items
    .flatMap((item) => item.allocations)
    .filter((a) => isReturnable(a) && a.handed_out_at && !a.returned_at),
)

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    selected: open.value.map((a) => a.id),
    damaged: [],
    notes: '',
    allocationNotes: {},
  })
})

function toggle(list: Id[], id: Id, on: boolean) {
  const index = list.indexOf(id)
  if (on && index < 0) list.push(id)
  if (!on && index >= 0) list.splice(index, 1)
}

async function save() {
  const all = form.selected.length === open.value.length
  const saved = await run(
    () =>
      requestsApi.returnDevices(props.assetRequest.id, {
        allocations: all ? null : form.selected,
        notes: form.notes,
        allocation_notes: form.selected
          .filter((id) => form.allocationNotes[id]?.trim())
          .map((id) => ({ allocation: id, note: form.allocationNotes[id]! })),
        damaged: form.damaged.filter((id) => form.selected.includes(id)),
      }),
    t('common.saved'),
  )
  if (saved) {
    show.value = false
    emit('saved', saved)
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('requests.actions.return')"
    style="max-width: 720px"
  >
    <p class="muted small hint">{{ t('requests.returning.hint') }}</p>
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <div v-for="allocation in open" :key="allocation.id" class="device">
        <NCheckbox
          :checked="form.selected.includes(allocation.id)"
          @update:checked="(on: boolean) => toggle(form.selected, allocation.id, on)"
        />
        <span class="mono">{{ allocationCode(allocation) }}</span>
        <span class="name">{{ allocationModel(allocation) }}</span>
        <NInput
          v-model:value="form.allocationNotes[allocation.id]"
          size="small"
          :disabled="!form.selected.includes(allocation.id)"
          :placeholder="t('requests.returning.notePlaceholder')"
        />
        <NCheckbox
          v-if="allocation.asset"
          :checked="form.damaged.includes(allocation.id)"
          :disabled="!form.selected.includes(allocation.id)"
          @update:checked="(on: boolean) => toggle(form.damaged, allocation.id, on)"
          >{{ t('requests.returning.damaged') }}</NCheckbox
        >
        <span v-else />
      </div>
      <NFormItem :label="t('common.notes')" class="notes">
        <NInput v-model:value="form.notes" type="textarea" :autosize="{ minRows: 2, maxRows: 5 }" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="!form.selected.length" @click="save">
          {{
            form.selected.length === open.length
              ? t('requests.actions.return')
              : t('requests.actions.returnSelected')
          }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.hint {
  margin: 0 0 10px;
}
.small {
  font-size: 11.5px;
}
.device {
  display: grid;
  grid-template-columns: 22px 90px minmax(0, 1fr) minmax(0, 1.2fr) 110px;
  gap: 10px;
  align-items: center;
  padding: 4px 0;
}
.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notes {
  margin-top: 12px;
}
</style>
