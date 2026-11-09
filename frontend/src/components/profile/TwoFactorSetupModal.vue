<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { Copy } from '@lucide/vue'
import { useIntervalFn } from '@vueuse/core'
import {
  NAlert,
  NButton,
  NCheckbox,
  NFormItem,
  NInput,
  NModal,
  NSteps,
  NStep,
  useMessage,
} from 'naive-ui'
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { twoFactorApi } from '@/api/auth'
import { ApiError } from '@/api/client'
import CodeInput from '@/components/common/CodeInput.vue'
import { showError } from '@/composables/useErrorPopover'

import BackupCodes from './BackupCodes.vue'

/**
 * Switches a method on (or changes to it): password, then the first code from
 * the app or the email, then the new backup codes.
 */
const props = defineProps<{ method: Schemas['TwoFactorMethod'] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ done: [] }>()
const { t } = useI18n()
const message = useMessage()

type Step = 'password' | 'verify' | 'codes'
const step = ref<Step>('password')
const stepIndex = computed(() => ({ password: 1, verify: 2, codes: 3 })[step.value])

const password = ref('')
const code = ref('')
const setup = ref<Schemas['TwoFactorSetupOut'] | null>(null)
const codes = ref<string[]>([])
const stored = ref(false)
const error = ref('')
const busy = ref(false)
const codeInput = ref<InstanceType<typeof CodeInput> | null>(null)

const RESEND_AFTER = 30
const resendIn = ref(0)
const { resume: startCountdown } = useIntervalFn(
  () => (resendIn.value = Math.max(0, resendIn.value - 1)),
  1000,
  { immediate: false },
)

watch(show, (visible) => {
  if (!visible) return
  step.value = 'password'
  password.value = code.value = error.value = ''
  setup.value = null
  codes.value = []
  stored.value = false
})

/** The app secret in groups of four, easier to type. */
const groupedSecret = computed(() => setup.value?.secret.match(/.{1,4}/g)?.join(' ') ?? '')

async function attempt(action: () => Promise<void>) {
  error.value = ''
  busy.value = true
  try {
    await action()
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e)
    // The setup expired or had too many wrong codes: start over.
    if (e instanceof ApiError && e.status === 409 && step.value === 'verify') {
      step.value = 'password'
      password.value = ''
    }
  } finally {
    busy.value = false
  }
}

const start = () =>
  attempt(async () => {
    setup.value = await twoFactorApi.setup(props.method, password.value)
    step.value = 'verify'
    code.value = ''
    if (props.method === 'email') {
      resendIn.value = RESEND_AFTER
      startCountdown()
    }
    await nextTick()
    codeInput.value?.focus()
  })

const confirm = () =>
  attempt(async () => {
    try {
      codes.value = (await twoFactorApi.confirm(code.value)).backup_codes
    } catch (e) {
      code.value = ''
      await nextTick()
      codeInput.value?.focus()
      throw e
    }
    step.value = 'codes'
    // Switched on already; the last step only shows the codes.
    emit('done')
  })

const resend = () =>
  attempt(async () => {
    setup.value = await twoFactorApi.resendSetupCode()
    resendIn.value = RESEND_AFTER
    startCountdown()
  })

function onComplete() {
  if (!busy.value) confirm()
}

async function copySecret() {
  try {
    await navigator.clipboard.writeText(setup.value?.secret ?? '')
    message.success(t('profile.security.copied'))
  } catch {
    showError(t('common.error'))
  }
}

const title = computed(() => t(`profile.security.setup.${props.method}Title`))
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="title"
    style="max-width: 560px"
    :mask-closable="step !== 'codes'"
    :closable="step !== 'codes'"
  >
    <NSteps :current="stepIndex" size="small" class="steps">
      <NStep :title="t('profile.security.setup.stepPassword')" />
      <NStep :title="t('profile.security.setup.stepVerify')" />
      <NStep :title="t('profile.security.setup.stepCodes')" />
    </NSteps>

    <NAlert v-if="error" type="error" :bordered="false" class="alert">{{ error }}</NAlert>

    <form v-if="step === 'password'" @submit.prevent="start">
      <p class="muted text">{{ t('profile.security.setup.passwordText') }}</p>
      <NFormItem :label="t('auth.password')" :show-feedback="false">
        <NInput
          v-model:value="password"
          type="password"
          show-password-on="click"
          placeholder=""
          autofocus
          :input-props="{ autocomplete: 'current-password' }"
        />
      </NFormItem>
      <div class="row actions">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" attr-type="submit" :disabled="!password" :loading="busy">
          {{ t('profile.security.setup.next') }}
        </NButton>
      </div>
    </form>

    <form v-else-if="step === 'verify' && setup" @submit.prevent="confirm">
      <p v-if="method === 'totp'" class="muted text">
        {{ t('profile.security.setup.scanText') }}
      </p>
      <template v-else>
        <NAlert v-if="!setup.code_sent" type="warning" :bordered="false" class="alert">
          {{ t('profile.security.setup.emailFailed') }}
        </NAlert>
        <p v-else class="muted text">
          {{ t('profile.security.setup.emailText', { email: setup.email_hint }) }}
        </p>
      </template>
      <!-- App: QR code on the left, key and code field on the right. -->
      <div :class="{ qr: method === 'totp' }">
        <img
          v-if="method === 'totp'"
          :src="setup.qr_svg"
          :alt="t('profile.security.setup.qrAlt')"
          width="200"
          height="200"
        />
        <div class="side">
          <div v-if="method === 'totp'" class="secret">
            <small class="muted">{{ t('profile.security.setup.manualText') }}</small>
            <div class="row">
              <code class="mono">{{ groupedSecret }}</code>
              <NButton
                quaternary
                size="tiny"
                :title="t('profile.security.copy')"
                @click="copySecret"
              >
                <template #icon><Copy :size="13" /></template>
              </NButton>
            </div>
          </div>
          <NFormItem :label="t('auth.twoFactor.code')" :show-feedback="false">
            <CodeInput
              ref="codeInput"
              v-model="code"
              :label="t('auth.twoFactor.code')"
              @complete="onComplete"
            />
          </NFormItem>
        </div>
      </div>
      <div class="row actions">
        <NButton
          v-if="method === 'email'"
          text
          size="small"
          class="resend"
          :disabled="resendIn > 0 || busy"
          @click="resend"
        >
          {{
            resendIn > 0
              ? t('auth.twoFactor.resendIn', { seconds: resendIn })
              : t('auth.twoFactor.resend')
          }}
        </NButton>
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" attr-type="submit" :disabled="code.length < 6" :loading="busy">
          {{ t('profile.security.setup.activate') }}
        </NButton>
      </div>
    </form>

    <div v-else-if="step === 'codes'">
      <NAlert type="success" :bordered="false" class="alert">
        {{ t('profile.security.setup.activated') }}
      </NAlert>
      <p class="muted text">{{ t('profile.security.codesText') }}</p>
      <BackupCodes :codes="codes" />
      <NCheckbox v-model:checked="stored" class="stored">
        {{ t('profile.security.codesStored') }}
      </NCheckbox>
      <div class="row actions">
        <NButton type="primary" :disabled="!stored" @click="show = false">
          {{ t('profile.security.finish') }}
        </NButton>
      </div>
    </div>
  </NModal>
</template>

<style scoped>
/* The steps share the full width; the connecting lines take the space between them. */
.steps {
  width: 100%;
  margin-bottom: 20px;
}
.steps :deep(.n-step) {
  flex: 1 1 0;
}
.steps :deep(.n-step:last-child) {
  flex: 0 0 auto;
}
/* Phones: only the current step keeps its title. */
@media (max-width: 480px) {
  .steps :deep(.n-step:not(.n-step--process-status) .n-step-content) {
    display: none;
  }
}
.text {
  margin: 0 0 14px;
  line-height: 1.5;
}
.alert {
  margin-bottom: 12px;
}
.qr {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 16px 20px;
}
.qr img {
  flex: none;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  /* The QR code needs its light background in dark mode too. */
  background: #fff;
}
/* Key at the top, code field at the bottom, level with the QR code. */
.qr .side {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
  min-width: 0;
  flex: 1 1 240px;
}
.qr .side :deep(.box) {
  height: 40px;
  font-size: 18px;
}
.secret {
  display: grid;
  gap: 6px;
}
.secret code {
  font-size: 13px;
  word-break: break-all;
}
.stored {
  margin-top: 14px;
}
.actions {
  justify-content: flex-end;
  margin-top: 18px;
}
.resend {
  margin-right: auto;
}
</style>
