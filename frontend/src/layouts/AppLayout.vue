<script setup lang="ts">
import { PanelLeftClose, PanelLeftOpen } from '@lucide/vue'
import { useBreakpoints, useStorage } from '@vueuse/core'
import { NButton, NLayout, NLayoutContent, NLayoutHeader, NLayoutSider } from 'naive-ui'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppSidebar from '@/components/layout/AppSidebar.vue'
import GlobalScan from '@/components/layout/GlobalScan.vue'
import UserMenu from '@/components/layout/UserMenu.vue'
import { useAuthStore } from '@/stores/auth'
import { useLiveStore } from '@/stores/live'

const { t } = useI18n()
const auth = useAuthStore()
// Live updates for the pages of the signed-in user; signing out leaves this layout.
const live = useLiveStore()
onMounted(live.start)
onUnmounted(live.stop)
const preferCollapsed = useStorage('argus.sidebar-collapsed', false)
const small = useBreakpoints({ tablet: 960 }).smaller('tablet')
// Small screens always start collapsed; the stored preference applies on wide screens.
const collapsed = ref(small.value || preferCollapsed.value)

watch(small, (isSmall) => (collapsed.value = isSmall || preferCollapsed.value))

function toggleSidebar() {
  collapsed.value = !collapsed.value
  if (!small.value) preferCollapsed.value = collapsed.value
}
</script>

<template>
  <NLayout has-sider class="shell">
    <NLayoutSider
      bordered
      collapse-mode="width"
      :collapsed-width="56"
      :width="232"
      :collapsed="collapsed"
      content-style="height: 100%; overflow: hidden"
    >
      <AppSidebar :collapsed="collapsed" />
    </NLayoutSider>
    <NLayout>
      <NLayoutHeader bordered class="topbar">
        <NButton quaternary size="small" :title="t('nav.collapse')" @click="toggleSidebar">
          <template #icon>
            <component :is="collapsed ? PanelLeftOpen : PanelLeftClose" :size="16" />
          </template>
        </NButton>
        <GlobalScan v-if="auth.can('assets')" />
        <div class="spacer" />
        <UserMenu />
      </NLayoutHeader>
      <NLayoutContent class="content" :native-scrollbar="false">
        <div class="grid-bg" />
        <RouterView v-slot="{ Component, route }">
          <component :is="Component" :key="route.fullPath" />
        </RouterView>
      </NLayoutContent>
    </NLayout>
  </NLayout>
</template>

<style scoped>
.shell {
  height: 100vh;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  height: var(--ar-header-height);
  padding: 0 16px 0 10px;
}
.spacer {
  flex: 1;
}
.content {
  position: relative;
  height: calc(100vh - var(--ar-header-height));
}
/* Subtle engineering grid behind the content. */
.grid-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(var(--ar-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--ar-grid) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: linear-gradient(to bottom, black, transparent 420px);
}
</style>
