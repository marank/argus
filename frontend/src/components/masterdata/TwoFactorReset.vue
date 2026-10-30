<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { ShieldCheck, ShieldOff } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useAuthStore } from '@/stores/auth'

/** Two-factor state of an employee in the edit drawer; IT resets it when the phone is lost. */
const props = defineProps<{
  form: Record<string, unknown>
  row?: Schemas['UserOut'] | null
  readonly?: boolean
}>()
const { t } = useI18n()
const auth = useAuthStore()
const confirm = useConfirm()
const { busy, run } = useAction()

const method = ref(props.row?.two_factor ?? null)
watch(
  () => props.row,
  (row) => (method.value = row?.two_factor ?? null),
)

// Own 2FA is switched off in the profile (with the password); the server checks the rest.
const canReset = () => !props.readonly && !!props.row && props.row.id !== auth.user?.id

async function reset() {
  if (!props.row || !(await confirm(t('masterdata.twoFactor.confirmReset'), { danger: true })))
    return
  const saved = await run(
    () => usersApi.resetTwoFactor(props.row!.id),
    t('masterdata.twoFactor.wasReset'),
  )
  if (saved) method.value = null
}
</script>

<template>
  <div v-if="row" class="two-factor">
    <span class="state">
      <component :is="method ? ShieldCheck : ShieldOff" :size="14" />
      {{ t('masterdata.twoFactor.label') }}:
      {{ method ? t(`profile.security.methods.${method}`) : t('masterdata.twoFactor.off') }}
    </span>
    <NButton
      v-if="method && canReset()"
      size="small"
      type="error"
      secondary
      :loading="busy"
      @click="reset"
    >
      {{ t('masterdata.twoFactor.reset') }}
    </NButton>
  </div>
</template>

<style scoped>
.two-factor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 12px;
  margin-top: 4px;
  padding: 10px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  font-size: 13px;
}
.state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
