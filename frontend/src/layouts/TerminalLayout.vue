<script setup lang="ts">
import { LogOut } from '@lucide/vue'
import { useIntervalFn } from '@vueuse/core'
import { NButton } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BrandMark from '@/components/common/BrandMark.vue'
import BrandWordmark from '@/components/common/BrandWordmark.vue'
import { useFormat } from '@/composables/useFormat'
import { useAuthStore } from '@/stores/auth'

/** Full-screen shell for the shared touch terminal: no navigation, large targets. */
const { t, locale } = useI18n()
const { longDate } = useFormat()
const auth = useAuthStore()
const router = useRouter()
const now = ref(new Date())
useIntervalFn(() => (now.value = new Date()), 15000)

async function logout() {
  await auth.logout()
  void router.push({ name: 'login' })
}

function toggleLanguage() {
  void auth.changeLanguage(locale.value === 'de' ? 'en' : 'de')
}
</script>

<template>
  <div class="terminal">
    <header>
      <RouterLink :to="{ name: 'terminal' }" class="brand">
        <BrandMark :size="28" />
        <BrandWordmark :height="18" class="wordmark" />
        <span class="eyebrow">{{ t('terminal.title') }}</span>
      </RouterLink>
      <div class="right">
        <span class="mono clock">{{ longDate(now, true) }}</span>
        <NButton quaternary @click="toggleLanguage">{{ locale === 'de' ? 'EN' : 'DE' }}</NButton>
        <NButton v-if="auth.isTerminal" quaternary :title="t('nav.logout')" @click="logout">
          <template #icon><LogOut :size="18" /></template>
        </NButton>
        <RouterLink v-else to="/"
          ><NButton quaternary>{{ t('terminal.backToApp') }}</NButton></RouterLink
        >
      </div>
    </header>
    <main>
      <RouterView v-slot="{ Component, route }">
        <component :is="Component" :key="route.fullPath" />
      </RouterView>
    </main>
  </div>
</template>

<style scoped>
.terminal {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--ar-bg);
  background-image:
    linear-gradient(var(--ar-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--ar-grid) 1px, transparent 1px);
  background-size: 32px 32px;
  font-size: 16px;
  user-select: none;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--ar-border);
  background: var(--ar-surface);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--ar-primary);
  text-decoration: none;
}
.wordmark {
  color: var(--ar-text);
}
.right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.clock {
  color: var(--ar-text-muted);
  font-size: 14px;
  margin-right: 8px;
}
main {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}
</style>
