<script setup lang="ts">
import { NAlert, NButton, NFormItem, NInput, NModal } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'

/** Asks for the password before a change to the sign-in; `action` gets it and may fail. */
const props = defineProps<{
  title: string
  text: string
  confirmLabel: string
  danger?: boolean
  action: (password: string) => Promise<unknown>
}>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ done: [result: unknown] }>()
const { t } = useI18n()

const password = ref('')
const error = ref('')
const busy = ref(false)

watch(show, (visible) => {
  if (visible) password.value = error.value = ''
})

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const result = await props.action(password.value)
    show.value = false
    emit('done', result)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <NModal v-model:show="show" preset="card" :title="title" style="max-width: 440px">
    <form @submit.prevent="submit">
      <p class="muted text">{{ text }}</p>
      <NAlert v-if="error" type="error" :bordered="false" class="alert">{{ error }}</NAlert>
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
        <NButton
          :type="danger ? 'error' : 'primary'"
          attr-type="submit"
          :disabled="!password"
          :loading="busy"
        >
          {{ confirmLabel }}
        </NButton>
      </div>
    </form>
  </NModal>
</template>

<style scoped>
.text {
  margin: 0 0 14px;
  line-height: 1.5;
}
.alert {
  margin-bottom: 12px;
}
.actions {
  justify-content: flex-end;
  margin-top: 18px;
}
</style>
