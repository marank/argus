<script setup lang="ts">
import {
  dateDeDE,
  dateEnUS,
  deDE,
  enUS,
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NLoadingBarProvider,
  NMessageProvider,
} from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import ErrorPopover from '@/components/common/ErrorPopover.vue'
import { useTheme } from '@/theme/useTheme'

const { naiveTheme, overrides } = useTheme()
const { locale } = useI18n()

const withoutInputPlaceholder = (base: typeof enUS) => ({
  ...base,
  Input: { ...base.Input, placeholder: '' },
  InputNumber: { ...base.InputNumber, placeholder: '' },
})
const naiveLocale = computed(() => withoutInputPlaceholder(locale.value === 'de' ? deDE : enUS))
const naiveDateLocale = computed(() => (locale.value === 'de' ? dateDeDE : dateEnUS))
</script>

<template>
  <NConfigProvider
    :theme="naiveTheme"
    :theme-overrides="overrides"
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    inline-theme-disabled
  >
    <NGlobalStyle />
    <NLoadingBarProvider>
      <NMessageProvider placement="top" :max="3">
        <NDialogProvider>
          <RouterView />
          <ErrorPopover />
        </NDialogProvider>
      </NMessageProvider>
    </NLoadingBarProvider>
  </NConfigProvider>
</template>
