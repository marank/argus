<script setup lang="ts">
import { NSwitch } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { NotificationAudience, NotificationChannel } from '@/types/settings'

import SettingRow from './SettingRow.vue'
import SettingsGroup from './SettingsGroup.vue'

export interface ChannelState {
  value: boolean
  disabled?: boolean
}

export interface NotificationGroup {
  audience: NotificationAudience
  description: string
  events: string[]
}

/**
 * Notification kinds by audience, with one switch per channel: email and in the app.
 * Used site-wide (settings) and per person (profile); `state` says what each switch shows.
 */
defineProps<{
  groups: NotificationGroup[]
  state: (key: string, channel: NotificationChannel) => ChannelState
}>()
const emit = defineEmits<{
  toggle: [key: string, channel: NotificationChannel, value: boolean]
}>()
const { t } = useI18n()

const CHANNELS: NotificationChannel[] = ['mail', 'app']
</script>

<template>
  <SettingsGroup
    v-for="group in groups"
    :key="group.audience"
    :title="t(`settings.mail.audience.${group.audience}`)"
    :description="group.description"
  >
    <div class="head" aria-hidden="true">
      <span v-for="channel in CHANNELS" :key="channel">{{
        t(`notifications.channel.${channel}`)
      }}</span>
    </div>
    <SettingRow
      v-for="key in group.events"
      :key="key"
      :label="t(`notifications.${key}`)"
      :help="t(`notifications.${key}Help`)"
      toggle
    >
      <div class="switches">
        <span v-for="channel in CHANNELS" :key="channel">
          <NSwitch
            :value="state(key, channel).value"
            :disabled="state(key, channel).disabled"
            :aria-label="`${t(`notifications.${key}`)}: ${t(`notifications.channel.${channel}`)}`"
            @update:value="(value: boolean) => emit('toggle', key, channel, value)"
          />
        </span>
      </div>
    </SettingRow>
  </SettingsGroup>
</template>

<style scoped>
.head,
.switches {
  display: grid;
  grid-template-columns: repeat(2, 76px);
  justify-items: center;
}
.head {
  justify-content: end;
  padding: 8px 0 6px;
  border-bottom: 1px solid var(--ar-border);
  color: var(--ar-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
/* The first row sits under the column titles, not under a divider of its own. */
.head + :deep(.setting-row) {
  border-top: none;
}
</style>
