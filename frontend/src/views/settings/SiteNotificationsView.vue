<script setup lang="ts">
import { NAlert, NButton, NSkeleton } from 'naive-ui'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { notificationSettingsApi } from '@/api/settings'
import NotificationMatrix, {
  type NotificationGroup,
} from '@/components/settings/NotificationMatrix.vue'
import { useAction } from '@/composables/useAction'
import { useFeaturesStore } from '@/stores/features'
import type { Schemas } from '@/api/types'
import type { NotificationChannel } from '@/types/settings'

/** Which notifications exist at all, per channel; people switch off what is on here. */
const { t } = useI18n()
const features = useFeaturesStore()
const { busy, run } = useAction()

const loaded = ref<Schemas['NotificationSettingsOut'] | null>(null)
const form = reactive({
  mail: {} as Record<string, boolean>,
  app: {} as Record<string, boolean>,
})

function apply(settings: Schemas['NotificationSettingsOut']) {
  loaded.value = settings
  form.mail = { ...settings.mail }
  form.app = { ...settings.app }
}

onMounted(async () => {
  apply(await notificationSettingsApi.get())
  if (!features.settings) await features.load()
})

const groups = computed<NotificationGroup[]>(() => {
  const events = features.settings?.notifications ?? []
  return (['employee', 'approver', 'it'] as const).map((audience) => ({
    audience,
    description: t(`settings.mail.audience.${audience}Description`),
    events: events.filter((e) => e.audience === audience).map((e) => e.key),
  }))
})

const state = (key: string, channel: NotificationChannel) => ({
  value: form[channel][key] ?? false,
})

async function save() {
  const saved = await run(() => notificationSettingsApi.update(form), t('common.saved'))
  if (saved) {
    apply(saved)
    features.load()
  }
}
</script>

<template>
  <NSkeleton v-if="!loaded" height="320px" />
  <form v-else @submit.prevent="save">
    <NAlert v-if="!loaded.mail_ready" type="info" :bordered="false" class="gap">
      {{ t('settings.notifications.mailNotReady') }}
      <RouterLink :to="{ name: 'settings-mail' }">{{ t('settings.sections.mail') }}</RouterLink>
    </NAlert>
    <NotificationMatrix
      :groups="groups"
      :state="state"
      @toggle="(key, channel, value) => (form[channel][key] = value)"
    />
    <div class="actions">
      <NButton type="primary" attr-type="submit" :loading="busy">{{ t('common.save') }}</NButton>
    </div>
  </form>
</template>

<style scoped>
.gap {
  margin-bottom: 8px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--ar-border);
}
</style>
