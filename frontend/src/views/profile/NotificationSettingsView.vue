<script setup lang="ts">
import { NAlert, NSkeleton, useMessage } from 'naive-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import PageHeader from '@/components/common/PageHeader.vue'
import NotificationMatrix, {
  type NotificationGroup,
} from '@/components/settings/NotificationMatrix.vue'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { NotificationChannel, NotificationKey } from '@/types/settings'

/**
 * Which notifications the user wants, by email and in the app. IT and approver
 * notifications only show to IT staff and approvers. A kind switched off site-wide in
 * both channels is not shown; in one channel, that switch shows off and locked. Without
 * a mail setup (or an address of their own) all email switches show off and locked.
 */
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()
const features = useFeaturesStore()

onMounted(() => features.load())

const site = computed(
  () => new Map((features.settings?.notifications ?? []).map((event) => [event.key, event])),
)
const mailPossible = computed(() => !!features.settings?.mail_enabled && !!auth.user?.email)

const groups = computed<NotificationGroup[]>(() => {
  const events = (features.settings?.notifications ?? []).filter((e) => e.mail || e.app)
  const shown = { employee: true, it: auth.isItStaff, approver: auth.isApprover }
  return (['employee', 'approver', 'it'] as const)
    .filter((audience) => shown[audience])
    .map((audience) => ({
      audience,
      description: t(`profile.notifications.${audience}Description`),
      events: events.filter((e) => e.audience === audience).map((e) => e.key),
    }))
    .filter((group) => group.events.length)
})

const stored = (channel: NotificationChannel) =>
  (channel === 'mail' ? auth.user?.notification_settings : auth.user?.app_notification_settings) ??
  {}

function state(key: NotificationKey, channel: NotificationChannel) {
  const available = !!site.value.get(key)?.[channel] && (channel === 'app' || mailPossible.value)
  return available ? { value: stored(channel)[key] ?? true } : { value: false, disabled: true }
}

async function toggle(key: NotificationKey, channel: NotificationChannel, value: boolean) {
  try {
    await auth.changeNotifications({
      notification_settings: auth.user?.notification_settings ?? {},
      app_notification_settings: auth.user?.app_notification_settings ?? {},
      [channel === 'mail' ? 'notification_settings' : 'app_notification_settings']: {
        ...stored(channel),
        [key]: value,
      },
    })
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
      <NAlert v-if="!groups.length" type="info" :bordered="false" class="gap">
        {{ t('profile.notifications.noneActive') }}
      </NAlert>
      <NotificationMatrix :groups="groups" :state="state" @toggle="toggle" />
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
</style>
