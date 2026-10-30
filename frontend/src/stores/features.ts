import { defineStore } from 'pinia'
import { computed, ref, watchEffect } from 'vue'

import { siteSettingsApi } from '@/api/settings'
import type { Schemas } from '@/api/types'
import type { FlagKey } from '@/types/settings'

/**
 * Modules and features switched on in the site settings. Until they are loaded
 * everything counts as on, so nothing flickers away for the common case.
 */
export const useFeaturesStore = defineStore('features', () => {
  const settings = ref<Schemas['SiteSettingsOut'] | null>(null)

  const isOn = (key: FlagKey) => settings.value?.flags[key] ?? true

  async function load() {
    settings.value = await siteSettingsApi.get()
  }

  async function update(flags: Schemas['SiteSettingsIn']['flags']) {
    settings.value = await siteSettingsApi.update({ flags })
  }

  async function updateRules(rules: Schemas['RulesSchema']) {
    settings.value = await siteSettingsApi.update({ rules })
  }

  const ldapEnabled = computed(() => settings.value?.ldap_enabled ?? false)

  /** Deadlines with defaults until the settings are loaded. */
  const rules = computed<Schemas['RulesSchema']>(
    () =>
      settings.value?.rules ?? {
        warranty_warning_days: 60,
        license_warning_days: 60,
        default_loan_days: 5,
        max_loan_days: 0,
        return_reminder_days: 2,
      },
  )

  // Attention animations (pulsing dots and tiles) can be switched off site-wide.
  watchEffect(() =>
    document.documentElement.classList.toggle('no-attention-motion', !isOn('attention_motion')),
  )

  return {
    settings,
    rules,
    ldapEnabled,
    isOn,
    load,
    update,
    updateRules,
    clear: () => (settings.value = null),
  }
})
