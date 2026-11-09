<script setup lang="ts">
import { NButton, NFormItem, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { toIsoDate } from '@/composables/useFormat'
import { useFeaturesStore } from '@/stores/features'
import type { Id } from '@/types/common'

/**
 * Assign a device from stock to an employee in one step: no request, no approval.
 * It is recorded as handed out, so a return date is watched like any loan.
 */
const props = defineProps<{ assetId: Id }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const features = useFeaturesStore()
const { busy, run } = useAction()

const startOfToday = () => new Date().setHours(0, 0, 0, 0)
const plusDays = (ts: number, days: number) => {
  const date = new Date(ts)
  date.setDate(date.getDate() + days)
  return date.getTime()
}

const form = reactive({
  requester: null as Id | null,
  duration: 'temporary' as Schemas['Duration'],
  end: null as number | null,
  // Left empty: from today. Earlier records an assignment that already began.
  start: null as number | null,
})

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    requester: null,
    duration: 'temporary',
    end: plusDays(startOfToday(), features.rules.default_loan_days - 1),
    start: null,
  })
})

const afterToday = (ts: number) => ts > startOfToday()
const beforeStart = (ts: number) => ts < Math.max(form.start ?? 0, startOfToday())

async function save() {
  const saved = await run(() =>
    requestsApi.quickAssign({
      asset: props.assetId,
      requester: form.requester!,
      duration: form.duration,
      start_date: toIsoDate(form.start),
      end_date: form.duration === 'temporary' ? toIsoDate(form.end) : null,
    }),
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
    :title="t('inventory.quickAssign.title')"
    style="max-width: 440px"
  >
    <p class="muted hint">{{ t('inventory.quickAssign.hint') }}</p>
    <div class="fields">
      <NFormItem :label="t('inventory.quickAssign.employee')" :show-feedback="false">
        <EntitySelect
          v-model="form.requester"
          :fetcher="usersApi.list"
          :params="{ is_active: true, is_terminal: false }"
          :label="(u) => u.display_name"
        />
      </NFormItem>
      <NFormItem :label="t('requests.duration')" :show-feedback="false">
        <NRadioGroup v-model:value="form.duration" class="duration">
          <NRadioButton value="temporary">{{ t('enums.duration.temporary') }}</NRadioButton>
          <NRadioButton value="permanent">{{ t('enums.duration.permanent') }}</NRadioButton>
        </NRadioGroup>
      </NFormItem>
      <NFormItem v-if="form.duration === 'temporary'" :show-feedback="false">
        <template #label>{{ t('inventory.quickAssign.returnDate') }}</template>
        <DateField v-model:value="form.end" :is-date-disabled="beforeStart" style="width: 100%" />
      </NFormItem>
      <NFormItem :show-feedback="false">
        <template #label>
          <FieldLabel
            :label="t('inventory.quickAssign.startDate')"
            :help="t('inventory.quickAssign.startDateHelp')"
          />
        </template>
        <DateField
          v-model:value="form.start"
          clearable
          :placeholder="t('inventory.quickAssign.today')"
          :is-date-disabled="afterToday"
          style="width: 100%"
        />
      </NFormItem>
    </div>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton
          type="primary"
          :disabled="!form.requester || (form.duration === 'temporary' && !form.end)"
          :loading="busy"
          @click="save"
          >{{ t('inventory.quickAssign.submit') }}</NButton
        >
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.hint {
  margin: 0 0 14px;
}
.fields {
  display: grid;
  gap: 14px;
}
.duration {
  display: flex;
  width: 100%;
}
.duration :deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}
</style>
