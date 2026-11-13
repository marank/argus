<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { KeyRound } from '@lucide/vue'
import { NButton, useMessage } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import NewPasswordModal from '@/components/profile/NewPasswordModal.vue'
import { useAuthStore } from '@/stores/auth'

/** Password state of a local account in the edit drawer; administrators set a new one. */
const props = defineProps<{
  row?: Schemas['UserOut'] | null
  readonly?: boolean
}>()
const { t } = useI18n()
const auth = useAuthStore()
const message = useMessage()

const hasPassword = ref(props.row?.has_password ?? false)
watch(
  () => props.row,
  (row) => (hasPassword.value = row?.has_password ?? false),
)
const show = ref(false)

// Directory accounts use the directory's password; the own one is changed in the profile.
const visible = computed(() => !!props.row && auth.isSuperuser && !props.row.is_ldap_user)
const canSet = computed(() => !props.readonly && props.row?.id !== auth.user?.id)

async function setPassword(password: string) {
  return usersApi.setPassword(props.row!.id, password)
}

function onDone() {
  hasPassword.value = true
  message.success(t('masterdata.password.saved'))
}
</script>

<template>
  <div v-if="visible" class="password">
    <span class="state">
      <KeyRound :size="14" />
      {{ t('masterdata.password.label') }}:
      {{ hasPassword ? t('masterdata.password.set') : t('masterdata.password.notSet') }}
    </span>
    <NButton v-if="canSet" size="small" secondary @click="show = true">
      {{ t('masterdata.password.setButton') }}
    </NButton>
    <NewPasswordModal
      v-model:show="show"
      :title="t('masterdata.password.title')"
      :text="t('masterdata.password.text', { name: row!.display_name })"
      :confirm-label="t('masterdata.password.setButton')"
      :action="setPassword"
      @done="onDone"
    />
  </div>
</template>

<style scoped>
.password {
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
