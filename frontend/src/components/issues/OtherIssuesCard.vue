<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'

/** Earlier and parallel reports on the same device (only shown when there are any). */
defineProps<{
  issues: Schemas['AssetIssueDetailOut']['other_issues']
  route: 'issue' | 'portal-issue'
}>()
const { t } = useI18n()
const { date, enumLabel } = useFormat()
</script>

<template>
  <NCard :title="t('inventory.issues.detail.otherIssues')" size="small">
    <ul class="others">
      <li v-for="other in issues" :key="other.id">
        <RouterLink :to="{ name: route, params: { id: other.id } }" class="other">
          <div class="head">
            <StatusTag group="issueStatus" :value="other.status" />
            <span class="small">{{ enumLabel('issueKind', other.kind) }}</span>
            <span class="mono muted small date">{{ date(other.created_at) }}</span>
          </div>
          <p class="text small">{{ other.description }}</p>
        </RouterLink>
      </li>
    </ul>
  </NCard>
</template>

<style scoped>
.others {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}
.others li + li {
  border-top: 1px solid var(--ar-border);
}
.other {
  display: block;
  padding: 8px 0;
  color: inherit;
  text-decoration: none;
}
.other:hover .text {
  color: var(--ar-text);
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.date {
  margin-left: auto;
}
.text {
  margin: 4px 0 0;
  color: var(--ar-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
