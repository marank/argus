<script setup lang="ts">
import { NButton, NModal } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import { useAction } from '@/composables/useAction'
import type { HandoverMode, Reservation } from '@/types/reservations'

import HandoverModeSelect from './HandoverModeSelect.vue'

const props = defineProps<{ reservation: Reservation }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const mode = ref<HandoverMode>('pickup')
watch(show, (visible) => visible && (mode.value = props.reservation.handover_mode))

async function save() {
  const saved = await run(
    () => reservationsApi.markReady(props.reservation.id, mode.value),
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
    :title="t('reservations.actions.markReady')"
    style="max-width: 560px"
  >
    <p class="muted">{{ t('handover.readyHint') }}</p>
    <HandoverModeSelect v-model="mode" />
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">{{
          t('reservations.actions.markReady')
        }}</NButton>
      </div>
    </template>
  </NModal>
</template>
