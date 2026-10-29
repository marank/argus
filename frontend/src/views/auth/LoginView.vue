<script setup lang="ts">
import { ArrowLeft, LogIn, ShieldCheck } from '@lucide/vue'
import { useIntervalFn } from '@vueuse/core'
import { NAlert, NButton, NForm, NFormItem, NInput } from 'naive-ui'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { authApi } from '@/api/auth'
import { ApiError, isUnreachable } from '@/api/client'
import BrandMark from '@/components/common/BrandMark.vue'
import CodeInput from '@/components/common/CodeInput.vue'
import { useAuthStore } from '@/stores/auth'
import type { TwoFactorChallenge } from '@/types/accounts'

const { t } = useI18n()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

/** Set once the password fits and the second step is due. */
const challenge = ref<TwoFactorChallenge | null>(null)
const code = ref('')
const useBackup = ref(false)
/** The digit boxes, or the text field for backup codes. */
const codeInput = ref<{ focus: () => void } | null>(null)
const CODE_LENGTH = 6
const BACKUP_LENGTH = 12

/** The server (or its database) does not answer; checked once on opening and with every attempt. */
const serverDown = ref(false)

async function checkServer() {
  try {
    await authApi.health()
  } catch (e) {
    serverDown.value = isUnreachable(e)
  }
}

onMounted(checkServer)

const RESEND_AFTER = 30
const resendIn = ref(0)
const { resume: startCountdown } = useIntervalFn(
  () => (resendIn.value = Math.max(0, resendIn.value - 1)),
  1000,
  { immediate: false },
)

const codeHint = computed(() => {
  if (!challenge.value) return ''
  if (useBackup.value) return t('auth.twoFactor.backupHint')
  if (challenge.value.two_factor === 'totp') return t('auth.twoFactor.totpHint')
  return challenge.value.code_sent
    ? t('auth.twoFactor.emailHint', { email: challenge.value.email_hint })
    : ''
})

const complete = computed(() =>
  useBackup.value
    ? code.value.replace(/[^0-9a-z]/gi, '').length >= BACKUP_LENGTH
    : code.value.length === CODE_LENGTH,
)

function proceed() {
  const next = typeof route.query.next === 'string' ? route.query.next : '/'
  // The Django admin signs in here too (see admin_login in the backend).
  if (next.startsWith('/admin/') && auth.isItStaff) window.location.assign(next)
  else router.replace(next)
}

async function attempt(action: () => Promise<void>) {
  error.value = ''
  busy.value = true
  try {
    await action()
    serverDown.value = false
  } catch (e) {
    serverDown.value = isUnreachable(e)
    // Shown as its own notice instead of an error.
    if (serverDown.value) return
    error.value = e instanceof ApiError ? e.message : String(e)
    // Expired or too many wrong codes (401, 429): the password has to be entered again.
    if (e instanceof ApiError && [401, 429].includes(e.status) && challenge.value) back()
  } finally {
    busy.value = false
  }
}

function startResendCountdown() {
  resendIn.value = RESEND_AFTER
  startCountdown()
}

const submit = () =>
  attempt(async () => {
    challenge.value = await auth.login(username.value, password.value)
    if (!challenge.value) return proceed()
    code.value = ''
    // Without a mailed code only a backup code helps.
    useBackup.value = challenge.value.two_factor === 'email' && !challenge.value.code_sent
    if (challenge.value.two_factor === 'email') startResendCountdown()
    await nextTick()
    codeInput.value?.focus()
  })

const verify = () =>
  attempt(async () => {
    try {
      await auth.verifyLogin(code.value)
    } catch (e) {
      code.value = ''
      await nextTick()
      codeInput.value?.focus()
      throw e
    }
    proceed()
  })

const resend = () =>
  attempt(async () => {
    challenge.value = await authApi.resendLoginCode()
    if (challenge.value.code_sent) useBackup.value = false
    startResendCountdown()
  })

/** App and email codes go out as soon as all boxes are filled. */
function onComplete() {
  if (!busy.value) verify()
}

async function toggleBackup() {
  useBackup.value = !useBackup.value
  code.value = ''
  await nextTick()
  codeInput.value?.focus()
}

function back() {
  challenge.value = null
  password.value = ''
  code.value = ''
}
</script>

<template>
  <div class="login">
    <div class="panel">
      <div class="brand">
        <BrandMark :size="36" />
        <div>
          <div class="wordmark">ARGUS</div>
          <div class="eyebrow">{{ t('auth.subtitle') }}</div>
        </div>
      </div>

      <h1>{{ challenge ? t('auth.twoFactor.title') : t('auth.title') }}</h1>

      <NAlert
        v-if="route.query.expired && !error && !challenge && !serverDown"
        type="warning"
        :bordered="false"
        class="alert"
      >
        {{ t('auth.sessionExpired') }}
      </NAlert>
      <NAlert v-if="serverDown" type="warning" :bordered="false" class="alert" role="status">
        {{ t('auth.serverDown') }}
      </NAlert>
      <NAlert v-if="error" type="error" :bordered="false" class="alert">{{ error }}</NAlert>
      <NAlert
        v-if="challenge?.two_factor === 'email' && !challenge.code_sent"
        type="warning"
        :bordered="false"
        class="alert"
      >
        {{ t('auth.twoFactor.emailFailed') }}
      </NAlert>

      <NForm v-if="challenge" @submit.prevent="verify">
        <p class="hint muted">{{ codeHint }}</p>
        <NFormItem
          :label="useBackup ? t('auth.twoFactor.backupCode') : t('auth.twoFactor.code')"
          :show-feedback="false"
          class="field"
        >
          <NInput
            v-if="useBackup"
            ref="codeInput"
            v-model:value="code"
            placeholder="xxxx-xxxx-xxxx"
            class="mono"
            :maxlength="20"
            :input-props="{ autocomplete: 'off', spellcheck: false }"
          />
          <CodeInput
            v-else
            ref="codeInput"
            v-model="code"
            :length="CODE_LENGTH"
            :label="t('auth.twoFactor.code')"
            @complete="onComplete"
          />
        </NFormItem>
        <NButton type="primary" attr-type="submit" block :loading="busy" :disabled="!complete">
          <template #icon><ShieldCheck :size="16" /></template>
          {{ t('auth.twoFactor.verify') }}
        </NButton>
        <div class="links">
          <NButton text size="small" @click="back">
            <template #icon><ArrowLeft :size="14" /></template>
            {{ t('common.back') }}
          </NButton>
          <span class="links-end">
            <NButton
              v-if="challenge.two_factor === 'email'"
              text
              size="small"
              :disabled="resendIn > 0 || busy"
              @click="resend"
            >
              {{
                resendIn > 0
                  ? t('auth.twoFactor.resendIn', { seconds: resendIn })
                  : t('auth.twoFactor.resend')
              }}
            </NButton>
            <NButton text size="small" type="primary" @click="toggleBackup">
              {{ useBackup ? t('auth.twoFactor.useCode') : t('auth.twoFactor.useBackup') }}
            </NButton>
          </span>
        </div>
      </NForm>

      <NForm v-else @submit.prevent="submit">
        <NFormItem :label="t('auth.username')" :show-feedback="false" class="field">
          <NInput
            v-model:value="username"
            placeholder=""
            autofocus
            :input-props="{ autocomplete: 'username' }"
          />
        </NFormItem>
        <NFormItem :label="t('auth.password')" :show-feedback="false" class="field">
          <NInput
            v-model:value="password"
            placeholder=""
            type="password"
            show-password-on="click"
            :input-props="{ autocomplete: 'current-password' }"
          />
        </NFormItem>
        <NButton
          type="primary"
          attr-type="submit"
          block
          :loading="busy"
          :disabled="!username || !password"
        >
          <template #icon><LogIn :size="16" /></template>
          {{ t('auth.signIn') }}
        </NButton>
      </NForm>
    </div>
    <div class="status mono" :class="{ down: serverDown }">
      {{ serverDown ? 'SYS · OFFLINE' : 'SYS · ONLINE' }}
    </div>
  </div>
</template>

<style scoped>
.login {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 16px;
  background-color: var(--ar-bg);
  background-image:
    linear-gradient(var(--ar-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--ar-grid) 1px, transparent 1px);
  background-size: 24px 24px;
}
.panel {
  width: 100%;
  max-width: 380px;
  padding: 28px;
  background: var(--ar-surface);
  border: 1px solid var(--ar-border);
  border-top: 3px solid var(--ar-primary);
  border-radius: 3px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--ar-primary);
}
.wordmark {
  font-family: var(--ar-font-mono);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0.3em;
  color: var(--ar-text);
}
h1 {
  margin: 26px 0 18px;
  font-size: 16px;
  font-weight: 600;
}
.field {
  margin-bottom: 14px;
}
.alert {
  margin-bottom: 14px;
}
.hint {
  margin: 0 0 14px;
  font-size: 12.5px;
  line-height: 1.5;
}
.links {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px 14px;
  margin-top: 16px;
}
.links-end {
  display: flex;
  gap: 14px;
}
.status {
  position: absolute;
  bottom: 14px;
  right: 18px;
  font-size: 10.5px;
  color: var(--ar-text-subtle);
  letter-spacing: 0.1em;
}
.status::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 6px;
  border-radius: 50%;
  background: var(--ar-success);
}
.status.down::before {
  background: var(--ar-error);
}
</style>
