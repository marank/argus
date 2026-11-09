<script setup lang="ts">
import { Trash2 } from '@lucide/vue'
import { NButton, NTimeline, NTimelineItem } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import { useFormat } from '@/composables/useFormat'
import { MANUAL_EVENT_KINDS } from '@/types/inventory'

defineProps<{
  events: Schemas['AssetEventOut'][]
  /** Entries recorded by hand can be deleted (needs the right to change devices). */
  editable: boolean
}>()
const emit = defineEmits<{ remove: [event: Schemas['AssetEventOut']] }>()
const { t } = useI18n()
const { dateTime, enumLabel, money } = useFormat()

const TYPES: Partial<
  Record<Schemas['AssetEventKind'], 'success' | 'info' | 'warning' | 'error' | 'default'>
> = {
  created: 'success',
  assigned: 'info',
  returned: 'default',
  reserved: 'info',
  replaced: 'info',
  component_replaced: 'warning',
  repair: 'error',
  maintenance: 'warning',
}
</script>

<template>
  <NTimeline size="medium">
    <NTimelineItem
      v-for="event in events"
      :key="event.id"
      :type="TYPES[event.kind] ?? 'default'"
      :time="dateTime(event.occurred_at)"
    >
      <template #header>
        <div class="head">
          <strong>{{ enumLabel('eventKind', event.kind) }}</strong>
          <span v-if="event.component_type || event.component" class="muted"
            >· {{ event.component_type?.name ?? event.component }}</span
          >
          <span v-if="event.component_serial || event.previous_serial" class="mono muted">{{
            event.previous_serial
              ? `${event.previous_serial} → ${event.component_serial || '—'}`
              : event.component_serial
          }}</span>
          <NButton
            v-if="editable && MANUAL_EVENT_KINDS.includes(event.kind)"
            quaternary
            size="tiny"
            class="remove"
            :title="t('common.delete')"
            @click="emit('remove', event)"
          >
            <template #icon><Trash2 :size="13" /></template>
          </NButton>
        </div>
      </template>
      <div class="body">
        <div v-if="event.description" class="desc">{{ event.description }}</div>
        <div class="meta muted">
          <span v-if="event.related_user"
            >{{ t('inventory.event.employee') }}: {{ event.related_user.display_name }}</span
          >
          <RouterLink
            v-if="event.related_asset"
            :to="{ name: 'asset', params: { id: event.related_asset.id } }"
            class="mono"
          >
            {{ event.related_asset.inventory_number
            }}{{ event.related_asset.name ? ` · ${event.related_asset.name}` : '' }}
          </RouterLink>
          <RouterLink
            v-if="event.asset_request"
            :to="{ name: 'request', params: { id: event.asset_request.id } }"
            class="mono"
          >
            {{ event.asset_request.number }}
          </RouterLink>
          <span v-if="event.cost">{{ money(event.cost) }}</span>
          <span v-if="event.performed_by"
            >{{ t('inventory.event.performedBy') }} {{ event.performed_by.display_name }}</span
          >
        </div>
      </div>
    </NTimelineItem>
  </NTimeline>
</template>

<style scoped>
.head {
  display: flex;
  align-items: center;
  gap: 6px;
}
.remove {
  margin-left: auto;
  opacity: 0.5;
}
.remove:hover {
  opacity: 1;
}
.desc {
  white-space: pre-line;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 12px;
  margin-top: 2px;
}
</style>
