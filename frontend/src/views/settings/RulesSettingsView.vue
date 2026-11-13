<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { NButton, NInputNumber, NSkeleton } from 'naive-ui'
import { onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAction } from '@/composables/useAction'
import { useFeaturesStore } from '@/stores/features'

/** Deadlines and warning periods in days, and how long a sign-in lasts in hours. */
const { t } = useI18n()
const features = useFeaturesStore()
const { busy, run } = useAction()

const form = reactive<Schemas['RulesSchema']>({ ...features.rules })
const loaded = ref(false)

onMounted(async () => {
  await features.load()
  Object.assign(form, features.rules)
  loaded.value = true
})
watch(
  () => features.rules,
  (rules) => Object.assign(form, rules),
)

async function save() {
  await run(() => features.updateRules({ ...form }))
}

const FIELDS: {
  key: keyof Schemas['RulesSchema']
  min: number
  max: number
  group: 'loans' | 'warnings' | 'signIn'
  unit?: 'hours'
}[] = [
  { key: 'default_loan_days', min: 1, max: 365, group: 'loans' },
  { key: 'max_loan_days', min: 0, max: 3650, group: 'loans' },
  { key: 'return_reminder_days', min: 0, max: 60, group: 'loans' },
  { key: 'warranty_warning_days', min: 1, max: 365, group: 'warnings' },
  { key: 'license_warning_days', min: 1, max: 365, group: 'warnings' },
  { key: 'session_hours', min: 1, max: 720, group: 'signIn', unit: 'hours' },
]
</script>

<template>
  <NSkeleton v-if="!loaded" height="320px" />
  <form v-else @submit.prevent="save">
    <SettingsGroup
      v-for="group in ['loans', 'warnings', 'signIn'] as const"
      :key="group"
      :title="t(`settings.rules.${group}`)"
      :description="t(`settings.rules.${group}Description`)"
    >
      <SettingRow
        v-for="field in FIELDS.filter((f) => f.group === group)"
        :key="field.key"
        :label="t(`settings.rules.${field.key}`)"
        :help="t(`settings.rules.${field.key}Help`)"
        toggle
      >
        <NInputNumber
          v-model:value="form[field.key]"
          :min="field.min"
          :max="field.max"
          :precision="0"
          size="small"
          style="width: 140px"
        >
          <template #suffix>{{ t(`settings.rules.${field.unit ?? 'days'}`) }}</template>
        </NInputNumber>
      </SettingRow>
    </SettingsGroup>
    <div class="actions">
      <NButton type="primary" attr-type="submit" :loading="busy">{{ t('common.save') }}</NButton>
    </div>
  </form>
</template>

<style scoped>
.actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--ar-border);
}
</style>
