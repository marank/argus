<script setup lang="ts">
import { Menu, PanelLeftClose, PanelLeftOpen } from '@lucide/vue'
import { useBreakpoints, useStorage } from '@vueuse/core'
import {
  NButton,
  NDrawer,
  NDrawerContent,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
} from 'naive-ui'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type RouteLocationNormalizedLoaded } from 'vue-router'

import BrandMark from '@/components/common/BrandMark.vue'

import AppSidebar from '@/components/layout/AppSidebar.vue'
import GlobalScan from '@/components/layout/GlobalScan.vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'
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
// Below 1280 px the content needs the room more than the menu needs its labels.
const breakpoints = useBreakpoints({ phone: 761, wide: 1280 })
const small = breakpoints.smaller('wide')
/** Phones have no sidebar at all: the menu comes in from the left on demand. */
const phone = breakpoints.smaller('phone')
const menuOpen = ref(false)
const route = useRoute()
const router = useRouter()
/**
 * Every address gets the page built anew, except for a step within it (`?step=`): that is
 * history inside the page, so the browser's back leads to the step before, not out of it.
 */
function viewKey(at: RouteLocationNormalizedLoaded): string {
  if (!('step' in at.query)) return at.fullPath
  const { step, ...query } = at.query
  void step
  return router.resolve({ path: at.path, query, hash: at.hash }).fullPath
}
watch(
  () => route.fullPath,
  () => (menuOpen.value = false),
)
watch(phone, (isPhone) => !isPhone && (menuOpen.value = false))
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
      v-if="!phone"
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
        <template v-if="phone">
          <NButton quaternary size="small" :title="t('nav.menu')" @click="menuOpen = true">
            <template #icon><Menu :size="18" /></template>
          </NButton>
          <RouterLink :to="{ name: 'dashboard' }" class="brand" :title="t('nav.dashboard')">
            <BrandMark :size="26" />
          </RouterLink>
        </template>
        <NButton v-else quaternary size="small" :title="t('nav.collapse')" @click="toggleSidebar">
          <template #icon>
            <component :is="collapsed ? PanelLeftOpen : PanelLeftClose" :size="16" />
          </template>
        </NButton>
        <GlobalScan v-if="auth.can('assets')" />
        <div class="spacer" />
        <NotificationBell />
        <UserMenu />
      </NLayoutHeader>
      <NLayoutContent class="content" :native-scrollbar="false">
        <div class="grid-bg" />
        <RouterView v-slot="{ Component, route }">
          <component :is="Component" :key="viewKey(route)" />
        </RouterView>
      </NLayoutContent>
    </NLayout>
    <NDrawer v-if="phone" v-model:show="menuOpen" placement="left" :width="260">
      <NDrawerContent :body-content-style="{ padding: 0, height: '100%' }">
        <AppSidebar :collapsed="false" />
      </NDrawerContent>
    </NDrawer>
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
.brand {
  display: flex;
  color: var(--ar-primary);
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
