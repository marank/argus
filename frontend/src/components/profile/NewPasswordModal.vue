<script setup lang="ts">
import { NAlert, NButton, NFormItem, NInput, NModal } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { ApiError } from '@/api/client'

/**
 * A new password, entered twice; with `withCurrent` also the current one (own password).
 * `action` gets the new and the current password and may fail with the broken rules.
 */
const props = defineProps<{
  title: string
  text: string
  confirmLabel: string
  withCurrent?: boolean
  action: (password: string, current: string) => Promise<unknown>
}>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ done: [result: unknown] }>()
const { t } = useI18n()

const current = ref('')
const password = ref('')
const repeat = ref('')
const error = ref('')
const busy = ref(false)

watch(show, (visible) => {
  if (visible) current.value = password.value = repeat.value = error.value = ''
})

const mismatch = computed(() => !!repeat.value && repeat.value !== password.value)
const ready = computed(
  () =>
    (!props.withCurrent || !!current.value) && !!password.value && password.value === repeat.value,
)

async function submit() {
  if (!ready.value) return
  error.value = ''
  busy.value = true
  try {
    const result = await props.action(password.value, current.value)
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
      <NFormItem v-if="withCurrent" :label="t('profile.security.password.current')">
        <NInput
          v-model:value="current"
          type="password"
          show-password-on="click"
          placeholder=""
          autofocus
          :input-props="{ autocomplete: 'current-password' }"
        />
      </NFormItem>
      <NFormItem :label="t('profile.security.password.new')">
        <NInput
          v-model:value="password"
          type="password"
          show-password-on="click"
          placeholder=""
          :autofocus="!withCurrent"
          :input-props="{ autocomplete: 'new-password' }"
        />
      </NFormItem>
      <NFormItem
        :label="t('profile.security.password.repeat')"
        :validation-status="mismatch ? 'error' : undefined"
        :feedback="mismatch ? t('profile.security.password.mismatch') : undefined"
      >
        <NInput
          v-model:value="repeat"
          type="password"
          show-password-on="click"
          placeholder=""
          :input-props="{ autocomplete: 'new-password' }"
        />
      </NFormItem>
      <small class="muted">{{ t('profile.security.password.rules') }}</small>
      <div class="row actions">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" attr-type="submit" :disabled="!ready" :loading="busy">
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
