<script setup lang="ts">
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="page">
    <div class="nf">
      <div class="code mono">404</div>
      <p>{{ t('common.notFound') }}</p>
      <RouterLink to="/"
        ><NButton>{{ t('common.goHome') }}</NButton></RouterLink
      >
    </div>
  </div>
</template>

<style scoped>
.nf {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 80px 0;
}
.code {
  font-size: 64px;
  font-weight: 700;
  color: var(--ar-text-subtle);
}
</style>
