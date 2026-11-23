<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { Bell, CheckCheck, Settings } from '@lucide/vue'
import { NBadge, NButton, NPopover, NScrollbar, NSpin } from 'naive-ui'
import { useDocumentVisibility } from '@vueuse/core'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { notificationsApi } from '@/api/notifications'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { useLiveStore } from '@/stores/live'
import { useNotificationsStore } from '@/stores/notifications'

/** The bell in the top bar: unread count, the latest notifications, a click opens the page. */
const { t } = useI18n()
const router = useRouter()
const store = useNotificationsStore()
const { relativeDay } = useFormat()

const open = ref(false)
const loading = ref(false)
const items = ref<Schemas['NotificationOut'][]>([])

async function load() {
  loading.value = true
  try {
    items.value = (await notificationsApi.list({ page_size: 20 })).items
  } finally {
    loading.value = false
  }
}

onMounted(store.refresh)
// New ones and those read in another tab; an open list follows along.
useLive(['notification'], () => {
  void store.refresh()
  if (open.value) void load()
})
// Without live updates the count follows on every page change and when the tab comes back.
const live = useLiveStore()
const route = useRoute()
const visibility = useDocumentVisibility()
watch([() => route.fullPath, visibility], ([, visible]) => {
  if (!live.connected && visible === 'visible') void store.refresh()
})

function toggle(show: boolean) {
  open.value = show
  if (show) {
    void load()
    void store.refresh()
  }
}

function choose(item: Schemas['NotificationOut']) {
  open.value = false
  if (!item.read_at) {
    item.read_at = new Date().toISOString()
    store.unread = Math.max(store.unread - 1, 0)
    notificationsApi.read(item.id).catch(() => store.refresh())
  }
  if (item.path) void router.push(item.path)
}

async function readAll() {
  const now = new Date().toISOString()
  items.value.forEach((item) => (item.read_at ??= now))
  store.unread = (await notificationsApi.readAll()).unread
}

function settings() {
  open.value = false
  void router.push({ name: 'profile-notifications' })
}
</script>

<template>
  <NPopover
    trigger="click"
    placement="bottom-end"
    :show="open"
    :show-arrow="false"
    style="padding: 0; width: 380px"
    @update:show="toggle"
  >
    <template #trigger>
      <NButton
        quaternary
        size="small"
        class="bell"
        :title="t('notifications.bell.title')"
        :aria-label="t('notifications.bell.title')"
      >
        <NBadge :value="store.unread" :max="99" :show="store.unread > 0" :offset="[2, -2]">
          <Bell :size="17" :stroke-width="1.8" />
        </NBadge>
      </NButton>
    </template>
    <div class="panel">
      <header>
        <strong>{{ t('notifications.bell.title') }}</strong>
        <div class="tools">
          <NButton
            v-if="store.unread"
            quaternary
            size="tiny"
            :title="t('notifications.bell.readAll')"
            @click="readAll"
          >
            <template #icon><CheckCheck :size="14" /></template>
            {{ t('notifications.bell.readAll') }}
          </NButton>
          <NButton
            quaternary
            size="tiny"
            :title="t('notifications.bell.settings')"
            :aria-label="t('notifications.bell.settings')"
            @click="settings"
          >
            <template #icon><Settings :size="14" /></template>
          </NButton>
        </div>
      </header>
      <NSpin :show="loading && !items.length" size="small">
        <NScrollbar style="max-height: 420px">
          <p v-if="!items.length && !loading" class="muted empty">
            {{ t('notifications.bell.empty') }}
          </p>
          <button
            v-for="item in items"
            :key="item.id"
            type="button"
            class="item"
            :class="{ unread: !item.read_at }"
            @click="choose(item)"
          >
            <span class="dot" aria-hidden="true" />
            <span class="body">
              <span class="title">{{ item.title }}</span>
              <span v-if="item.text" class="text muted">{{ item.text }}</span>
              <small class="muted">{{ relativeDay(item.created_at) }}</small>
            </span>
          </button>
        </NScrollbar>
      </NSpin>
    </div>
  </NPopover>
</template>

<style scoped>
.bell {
  margin-right: 6px;
}
.panel {
  display: grid;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px 10px 14px;
  border-bottom: 1px solid var(--ar-border);
}
.tools {
  display: flex;
  gap: 2px;
}
.empty {
  margin: 0;
  padding: 28px 16px;
  text-align: center;
}
.item {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr);
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  border-bottom: 1px solid var(--ar-border);
  background: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.item:last-child {
  border-bottom: none;
}
.item:hover,
.item:focus-visible {
  background: var(--ar-surface-sunken);
  outline: none;
}
.dot {
  width: 8px;
  height: 8px;
  margin-top: 5px;
  border-radius: 50%;
}
.unread .dot {
  background: var(--ar-primary);
}
.body {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.title {
  font-size: 13px;
}
.unread .title {
  font-weight: 600;
}
.text {
  display: -webkit-box;
  overflow: hidden;
  font-size: 12.5px;
  line-height: 1.4;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
small {
  font-size: 11px;
}
</style>
