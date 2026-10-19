<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { NAlert, NButton, NForm, NFormItem, NInput } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await auth.login(username.value, password.value)
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    router.replace(next)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="login">
    <div class="panel">
      <div class="brand">
        <svg viewBox="0 0 32 32" width="34" height="34" aria-hidden="true">
          <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" stroke-width="2.4" />
          <circle cx="16" cy="16" r="3.6" fill="currentColor" />
          <path
            d="M16 2v5M16 25v5M2 16h5M25 16h5"
            stroke="currentColor"
            stroke-width="2.4"
            stroke-linecap="round"
          />
        </svg>
        <div>
          <div class="wordmark">ARGUS</div>
          <div class="eyebrow">{{ t('auth.subtitle') }}</div>
        </div>
      </div>

      <h1>{{ t('auth.title') }}</h1>

      <NAlert v-if="route.query.expired && !error" type="warning" :bordered="false" class="alert">
        {{ t('auth.sessionExpired') }}
      </NAlert>
      <NAlert v-if="error" type="error" :bordered="false" class="alert">{{ error }}</NAlert>

      <NForm @submit.prevent="submit">
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
    <div class="status mono">SYS · ONLINE</div>
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
</style>
