<script setup lang="ts">
import { NButton, NInput, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { portalApi } from '@/api/reservations'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { ISSUE_KINDS, type IssueKind, type OwnIssue } from '@/types/inventory'
import type { MyAsset } from '@/types/reservations'
import { categoryIcon } from '@/utils/icons'

/** An employee reports a problem with one of their devices to IT. */
const props = defineProps<{ asset: MyAsset | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ reported: [issue: OwnIssue] }>()

const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const form = reactive({ kind: 'defect' as IssueKind, description: '' })
watch(show, (visible) => visible && Object.assign(form, { kind: 'defect', description: '' }))

async function send() {
  if (!props.asset) return
  const issue = await run(
    () => portalApi.reportIssue(props.asset!.id, { ...form }),
    t('reservations.myDevices.reportSent'),
  )
  if (issue) {
    emit('reported', issue)
    show.value = false
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('reservations.myDevices.report')"
    style="max-width: 520px"
  >
    <div class="form">
      <!-- Which device the report is about. -->
      <div v-if="asset" class="device">
        <span class="icon"
          ><component :is="categoryIcon(asset.category_icon)" :size="20" :stroke-width="1.5"
        /></span>
        <div class="device-text">
          <strong>{{ asset.model.full_name }}</strong>
          <span class="mono muted small">
            {{ asset.inventory_number }}
            <template v-if="asset.serial_number"> · {{ asset.serial_number }}</template>
          </span>
        </div>
      </div>
      <div class="field">
        <FieldLabel :label="t('reservations.myDevices.reportKind')" />
        <NRadioGroup v-model:value="form.kind" size="small">
          <NRadioButton v-for="kind in ISSUE_KINDS" :key="kind" :value="kind">
            {{ enumLabel('issueKind', kind) }}
          </NRadioButton>
        </NRadioGroup>
      </div>
      <div class="field">
        <FieldLabel :label="t('reservations.myDevices.reportDescription')" required />
        <NInput
          v-model:value="form.description"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 8 }"
          :maxlength="2000"
          :placeholder="t('reservations.myDevices.reportPlaceholder')"
        />
      </div>
    </div>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="!form.description.trim()" @click="send">
          {{ t('reservations.myDevices.send') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.form {
  display: grid;
  gap: 14px;
}
.field {
  display: grid;
  gap: 6px;
}
.device {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
.icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.device-text {
  display: grid;
  min-width: 0;
}
.small {
  font-size: 12px;
}
</style>
