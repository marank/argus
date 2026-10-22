<script setup lang="ts">
import { ChevronRight, PackageCheck, Search } from '@lucide/vue'
import { useDebounceFn, useIntervalFn } from '@vueuse/core'
import { NInput, NSpin } from 'naive-ui'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { terminalApi } from '@/api/requests'
import { useFormat } from '@/composables/useFormat'
import type { TerminalPickup } from '@/types/requests'

const { t } = useI18n()
const { weekday } = useFormat()

const pickups = ref<TerminalPickup[] | null>(null)
const search = ref('')

async function load() {
  pickups.value = await terminalApi.pickups(search.value || undefined)
}

onMounted(load)
watch(search, useDebounceFn(load, 250))
// New pickups prepared by IT appear without touching the screen.
useIntervalFn(load, 30000)
</script>

<template>
  <div class="list">
    <div class="intro">
      <h1>{{ t('terminal.welcome') }}</h1>
      <p class="muted">{{ t('terminal.welcomeHint') }}</p>
    </div>
    <NInput
      v-model:value="search"
      size="large"
      clearable
      :placeholder="t('terminal.search')"
      class="search"
    >
      <template #prefix><Search :size="20" /></template>
    </NInput>

    <NSpin v-if="!pickups" />
    <div v-else-if="!pickups.length" class="empty">
      <PackageCheck :size="48" :stroke-width="1.2" />
      <p>{{ t('terminal.empty') }}</p>
    </div>
    <div v-else class="cards">
      <RouterLink
        v-for="pickup in pickups"
        :key="pickup.id"
        :to="{ name: 'terminal-pickup', params: { id: pickup.id } }"
        class="card"
      >
        <div class="who">
          <strong>{{ pickup.requester.display_name }}</strong>
          <span class="muted">{{ pickup.requester.department?.name }}</span>
        </div>
        <div class="what">
          <span>{{ pickup.title }}</span>
          <small class="muted">{{ pickup.summary }}</small>
        </div>
        <div class="meta mono">
          <span>{{ pickup.number }}</span>
          <span v-if="pickup.pickup_at">{{ weekday(pickup.pickup_at) }}</span>
        </div>
        <ChevronRight :size="28" class="chevron" />
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.list {
  display: grid;
  gap: 20px;
}
h1 {
  margin: 0;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.intro p {
  margin: 6px 0 0;
  font-size: 17px;
}
.search :deep(input) {
  font-size: 18px;
}
.cards {
  display: grid;
  gap: 12px;
}
.card {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(0, 2fr) auto 32px;
  align-items: center;
  gap: 20px;
  min-height: 96px;
  padding: 18px 22px;
  border: 1px solid var(--ar-border);
  border-left: 4px solid var(--ar-success);
  border-radius: 4px;
  background: var(--ar-surface);
  color: inherit;
  text-decoration: none;
}
.card:active {
  background: var(--ar-primary-soft);
}
.who,
.what,
.meta {
  display: grid;
  gap: 4px;
}
.who strong {
  font-size: 21px;
}
.what span {
  font-size: 17px;
}
.meta {
  text-align: right;
  font-size: 13px;
  color: var(--ar-text-muted);
}
.chevron {
  color: var(--ar-text-subtle);
}
.empty {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 80px 0;
  color: var(--ar-text-subtle);
  font-size: 18px;
}
@media (max-width: 800px) {
  .card {
    grid-template-columns: 1fr 32px;
  }
  .what,
  .meta {
    grid-column: 1;
    text-align: left;
  }
  .chevron {
    grid-row: 1 / span 3;
    grid-column: 2;
  }
}
</style>
