<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { NButton, NInput, NInputNumber, NSelect, NSkeleton, NSwitch, useMessage } from 'naive-ui'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { mailSettingsApi } from '@/api/settings'
import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAction } from '@/composables/useAction'
import { showError } from '@/composables/useErrorPopover'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

/** SMTP server and sender; which notifications go out is set in its own section. */
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()
const features = useFeaturesStore()
const { busy, run } = useAction()

const loaded = ref<Schemas['MailSettingsOut'] | null>(null)
const form = reactive<Schemas['MailSettingsIn']>({
  enabled: false,
  host: '',
  port: 587,
  security: 'starttls',
  username: '',
  password: null,
  from_email: '',
  from_name: 'Argus',
  app_url: '',
})
const newPassword = ref('')
const testTo = ref('')
const testing = ref(false)

function apply(settings: Schemas['MailSettingsOut']) {
  loaded.value = settings
  Object.assign(form, {
    enabled: settings.enabled,
    host: settings.host,
    port: settings.port,
    security: settings.security,
    username: settings.username,
    password: null,
    from_email: settings.from_email,
    from_name: settings.from_name,
    app_url: settings.app_url,
  })
  newPassword.value = ''
}

onMounted(async () => {
  apply(await mailSettingsApi.get())
  testTo.value = auth.user?.email ?? ''
  if (!features.settings) await features.load()
})

const securityOptions = computed(() =>
  (['starttls', 'ssl', 'none'] as const).map((value) => ({
    value,
    label: t(`settings.mail.security.${value}`),
  })),
)

async function save() {
  const saved = await run(() =>
    mailSettingsApi.update({ ...form, password: newPassword.value || null }),
  )
  if (saved) {
    apply(saved)
    features.load()
  }
}

async function sendTest() {
  testing.value = true
  try {
    const result = await mailSettingsApi.test(testTo.value)
    message.success(result.detail)
  } catch (error) {
    showError(error instanceof Error ? error.message : t('common.error'))
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <NSkeleton v-if="!loaded" height="320px" />
  <form v-else @submit.prevent="save">
    <SettingsGroup
      :title="t('settings.mail.server')"
      :description="t('settings.mail.serverDescription')"
    >
      <SettingRow :label="t('settings.mail.enabled')" :help="t('settings.mail.enabledHelp')" toggle>
        <NSwitch v-model:value="form.enabled" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.host')" :required="form.enabled">
        <NInput v-model:value="form.host" placeholder="smtp.example.com" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.port')">
        <div class="pair">
          <NInputNumber v-model:value="form.port" :min="1" :max="65535" :show-button="false" />
          <NSelect v-model:value="form.security" :options="securityOptions" />
        </div>
      </SettingRow>
      <SettingRow :label="t('settings.mail.username')">
        <NInput v-model:value="form.username" :input-props="{ autocomplete: 'off' }" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.password')" :help="t('settings.mail.passwordHelp')">
        <NInput
          v-model:value="newPassword"
          type="password"
          show-password-on="click"
          :input-props="{ autocomplete: 'new-password' }"
          :placeholder="loaded?.password_set ? t('settings.mail.passwordSet') : ''"
        />
      </SettingRow>
    </SettingsGroup>

    <SettingsGroup
      :title="t('settings.mail.sender')"
      :description="t('settings.mail.senderDescription')"
    >
      <SettingRow :label="t('settings.mail.fromEmail')" :required="form.enabled">
        <NInput v-model:value="form.from_email" placeholder="argus@example.com" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.fromName')">
        <NInput v-model:value="form.from_name" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.appUrl')" :help="t('settings.mail.appUrlHelp')">
        <NInput v-model:value="form.app_url" placeholder="https://argus.example.com" />
      </SettingRow>
      <SettingRow :label="t('settings.mail.test')" :help="t('settings.mail.testHelp')">
        <div class="pair test">
          <NInput v-model:value="testTo" :placeholder="t('settings.mail.testTo')" />
          <NButton :loading="testing" :disabled="!testTo || !loaded?.host" @click="sendTest">
            {{ t('settings.mail.sendTest') }}
          </NButton>
        </div>
      </SettingRow>
    </SettingsGroup>

    <div class="actions">
      <NButton type="primary" attr-type="submit" :loading="busy">{{ t('common.save') }}</NButton>
    </div>
  </form>
</template>

<style scoped>
.pair {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 8px;
}
.pair.test {
  grid-template-columns: minmax(0, 1fr) auto;
}
.actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--ar-border);
}
</style>
