<script setup lang="ts">
import { KeyRound, Mail, ShieldCheck, Smartphone } from '@lucide/vue'
import { NAlert, NButton, NModal, NSkeleton, NTag, useMessage } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { twoFactorApi } from '@/api/auth'
import PageHeader from '@/components/common/PageHeader.vue'
import BackupCodes from '@/components/profile/BackupCodes.vue'
import PasswordConfirmModal from '@/components/profile/PasswordConfirmModal.vue'
import TwoFactorSetupModal from '@/components/profile/TwoFactorSetupModal.vue'
import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAuthStore } from '@/stores/auth'
import type { TwoFactorMethod, TwoFactorStatus } from '@/types/accounts'

/** The user's two-factor sign-in: app or email, backup codes, switching off. */
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()

const status = ref<TwoFactorStatus | null>(null)
const loadError = ref(false)

async function load() {
  try {
    status.value = await twoFactorApi.status()
    loadError.value = false
  } catch {
    loadError.value = true
  }
}
onMounted(load)

const METHODS: { key: TwoFactorMethod; icon: typeof Smartphone }[] = [
  { key: 'totp', icon: Smartphone },
  { key: 'email', icon: Mail },
]
const active = computed(() => status.value?.method ?? null)
const fewCodes = computed(() => !!active.value && (status.value?.backup_codes_left ?? 0) <= 2)

const setupMethod = ref<TwoFactorMethod>('totp')
const showSetup = ref(false)
function openSetup(method: TwoFactorMethod) {
  setupMethod.value = method
  showSetup.value = true
}

const showRenew = ref(false)
const showDisable = ref(false)
const newCodes = ref<string[]>([])
const showCodes = ref(false)

async function refresh() {
  await Promise.all([load(), auth.fetchCurrentUser()])
}

async function onRenewed(result: unknown) {
  newCodes.value = (result as { backup_codes: string[] }).backup_codes
  showCodes.value = true
  await load()
}

async function onDisabled() {
  message.success(t('profile.security.disabled'))
  await refresh()
}
</script>

<template>
  <div class="page narrow">
    <PageHeader :title="t('profile.security.title')" :subtitle="t('profile.security.subtitle')" />
    <NAlert v-if="loadError" type="error" :bordered="false">{{ t('common.error') }}</NAlert>
    <NSkeleton v-else-if="!status" height="240px" />
    <template v-else>
      <NAlert v-if="fewCodes" type="warning" :bordered="false" class="gap">
        {{ t('profile.security.fewCodes', { count: status.backup_codes_left }) }}
      </NAlert>

      <SettingsGroup
        :title="t('profile.security.twoFactor')"
        :description="t('profile.security.twoFactorDescription')"
      >
        <SettingRow :label="t('common.status')" toggle>
          <NTag v-if="active" type="success" size="small" :bordered="false">
            <template #icon><ShieldCheck :size="13" /></template>
            {{ t('profile.security.on', { method: t(`profile.security.methods.${active}`) }) }}
          </NTag>
          <NTag v-else size="small" :bordered="false">{{ t('profile.security.off') }}</NTag>
        </SettingRow>
        <SettingRow
          v-for="method in METHODS"
          :key="method.key"
          :label="t(`profile.security.methods.${method.key}`)"
          :help="t(`profile.security.methods.${method.key}Help`)"
          toggle
        >
          <div class="control">
            <small
              v-if="method.key === 'email' && !status.email_available && active !== 'email'"
              class="muted"
            >
              {{ t('profile.security.emailUnavailable') }}
            </small>
            <NTag v-if="active === method.key" type="success" size="small" :bordered="false">
              {{ t('profile.security.inUse') }}
            </NTag>
            <NButton
              v-else
              size="small"
              :type="active ? 'default' : 'primary'"
              :secondary="!!active"
              :disabled="method.key === 'email' && !status.email_available"
              @click="openSetup(method.key)"
            >
              <template #icon><component :is="method.icon" :size="14" /></template>
              {{ active ? t('profile.security.switchTo') : t('profile.security.setUp') }}
            </NButton>
          </div>
        </SettingRow>
      </SettingsGroup>

      <SettingsGroup
        v-if="active"
        :title="t('profile.security.backupCodes')"
        :description="t('profile.security.backupDescription')"
      >
        <SettingRow
          :label="
            t(
              'profile.security.codesLeft',
              { count: status.backup_codes_left },
              status.backup_codes_left,
            )
          "
          toggle
        >
          <NButton size="small" secondary @click="showRenew = true">
            <template #icon><KeyRound :size="14" /></template>
            {{ t('profile.security.renew') }}
          </NButton>
        </SettingRow>
        <SettingRow
          :label="t('profile.security.disable')"
          :help="t('profile.security.disableHelp')"
          toggle
        >
          <NButton size="small" type="error" secondary @click="showDisable = true">
            {{ t('profile.security.disable') }}
          </NButton>
        </SettingRow>
      </SettingsGroup>
    </template>

    <TwoFactorSetupModal v-model:show="showSetup" :method="setupMethod" @done="refresh" />
    <PasswordConfirmModal
      v-model:show="showRenew"
      :title="t('profile.security.renew')"
      :text="t('profile.security.renewText')"
      :confirm-label="t('profile.security.renew')"
      :action="twoFactorApi.renewBackupCodes"
      @done="onRenewed"
    />
    <PasswordConfirmModal
      v-model:show="showDisable"
      :title="t('profile.security.disable')"
      :text="t('profile.security.disableText')"
      :confirm-label="t('profile.security.disable')"
      danger
      :action="twoFactorApi.disable"
      @done="onDisabled"
    />
    <NModal
      v-model:show="showCodes"
      preset="card"
      :title="t('profile.security.backupCodes')"
      style="max-width: 520px"
    >
      <p class="muted text">{{ t('profile.security.codesText') }}</p>
      <BackupCodes :codes="newCodes" />
      <template #footer>
        <div class="row" style="justify-content: flex-end">
          <NButton type="primary" @click="showCodes = false">
            {{ t('profile.security.finish') }}
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.narrow {
  max-width: 900px;
}
.gap {
  margin-bottom: 8px;
}
.control {
  display: flex;
  align-items: center;
  gap: 10px;
}
small {
  /* Wraps instead of squeezing the label next to it. */
  max-width: 220px;
  font-size: 11.5px;
  line-height: 1.4;
  text-align: right;
}
.text {
  margin: 0 0 14px;
  line-height: 1.5;
}
</style>
