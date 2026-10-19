<script setup lang="ts">
import { computed } from 'vue'

import CrudPage from '@/components/crud/CrudPage.vue'
import NotFoundView from '@/views/NotFoundView.vue'

import { RESOURCES } from './resources'

const props = defineProps<{ resource: string }>()
const definition = computed(() => RESOURCES[props.resource])
</script>

<template>
  <CrudPage v-if="definition" :key="resource" :resource="definition" />
  <NotFoundView v-else />
</template>
