<script setup lang="ts">
import { NAlert, NSkeleton, NSwitch, useMessage } from 'naive-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import PageHeader from '@/components/common/PageHeader.vue'
import SettingRow from '@/components/settings/SettingRow.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { NotificationKey } from '@/types/settings'

/**
 * Which emails the user wants to receive. IT and approver notifications only show
 * to IT staff and approvers; kinds switched off site-wide are shown greyed out.
 */
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()
const features = useFeaturesStore()

onMounted(() => features.load())

const groups = computed(() => {
  const events = features.settings?.notifications ?? []
  const shown = { employee: true, it: auth.isItStaff, approver: auth.isApprover }
  return (['employee', 'approver', 'it'] as const)
    .filter((audience) => shown[audience])
    .map((audience) => ({ audience, events: events.filter((e) => e.audience === audience) }))
})

const wants = (key: NotificationKey) => auth.user?.notification_settings?.[key] ?? true

async function toggle(key: NotificationKey, value: boolean) {
  try {
    await auth.changeNotifications({ ...auth.user?.notification_settings, [key]: value })
    message.success(t('common.saved'))
  } catch {
    message.error(t('common.error'))
  }
}
</script>

<template>
  <div class="page narrow">
    <PageHeader
      :title="t('profile.notifications.title')"
      :subtitle="t('profile.notifications.subtitle', { email: auth.user?.email || '—' })"
    />
    <NSkeleton v-if="!features.settings" height="240px" />
    <template v-else>
      <NAlert v-if="!features.settings.mail_enabled" type="info" :bordered="false" class="gap">
        {{ t('profile.notifications.mailOff') }}
      </NAlert>
      <NAlert v-else-if="!auth.user?.email" type="warning" :bordered="false" class="gap">
        {{ t('profile.notifications.noEmail') }}
      </NAlert>
      <SettingsGroup
        v-for="group in groups"
        :key="group.audience"
        :title="t(`settings.mail.audience.${group.audience}`)"
        :description="t(`profile.notifications.${group.audience}Description`)"
      >
        <SettingRow
          v-for="event in group.events"
          :key="event.key"
          :label="t(`notifications.${event.key}`)"
          :help="t(`notifications.${event.key}Help`)"
          toggle
        >
          <div class="control">
            <small v-if="!event.enabled" class="muted">{{
              t('profile.notifications.siteOff')
            }}</small>
            <NSwitch
              :value="event.enabled && wants(event.key)"
              :disabled="!event.enabled || !features.settings.mail_enabled"
              @update:value="(value: boolean) => toggle(event.key, value)"
            />
          </div>
        </SettingRow>
      </SettingsGroup>
    </template>
  </div>
</template>

<style scoped>
.narrow {
  max-width: 900px;
}
.gap {
  margin-bottom: 8px;
}
.control {
  display: flex;
  align-items: center;
  gap: 10px;
}
small {
  font-size: 11.5px;
  white-space: nowrap;
}
</style>
