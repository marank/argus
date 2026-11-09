<script setup lang="ts">
import { Copy, Download } from '@lucide/vue'
import { NButton, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { showError } from '@/composables/useErrorPopover'
import { useAuthStore } from '@/stores/auth'

/** Freshly created backup codes: shown once, to copy or save as a text file. */
const props = defineProps<{ codes: string[] }>()
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()

function asText() {
  return [
    t('profile.security.codesFileTitle', { user: auth.user?.username ?? '' }),
    '',
    ...props.codes,
    '',
    t('profile.security.codesFileHint'),
  ].join('\n')
}

async function copy() {
  try {
    await navigator.clipboard.writeText(props.codes.join('\n'))
    message.success(t('profile.security.copied'))
  } catch {
    showError(t('common.error'))
  }
}

function download() {
  const url = URL.createObjectURL(new Blob([asText()], { type: 'text/plain;charset=utf-8' }))
  const link = Object.assign(document.createElement('a'), {
    href: url,
    download: `argus-backup-codes-${auth.user?.username ?? 'user'}.txt`,
  })
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="backup-codes">
    <ol class="codes mono">
      <li v-for="code in codes" :key="code">{{ code }}</li>
    </ol>
    <div class="row">
      <NButton size="small" secondary @click="copy">
        <template #icon><Copy :size="14" /></template>
        {{ t('profile.security.copy') }}
      </NButton>
      <NButton size="small" secondary @click="download">
        <template #icon><Download :size="14" /></template>
        {{ t('profile.security.download') }}
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.backup-codes {
  display: grid;
  gap: 12px;
}
.codes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 24px;
  margin: 0;
  padding: 14px 18px 14px 36px;
  background: var(--ar-bg);
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  font-size: 14px;
  letter-spacing: 0.05em;
}
.codes li::marker {
  color: var(--ar-text-subtle);
  font-size: 11px;
}
@media (max-width: 480px) {
  .codes {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
