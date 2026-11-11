<script setup lang="ts">
import type { Id } from '@/types/common'
import { h, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import ScanCombobox from '@/components/common/ScanCombobox.vue'
import { useAction } from '@/composables/useAction'
import { useScanner } from '@/composables/useScanner'
import { categoryIcon } from '@/utils/icons'
import { itemLabel } from '@/utils/requests'

/**
 * One scan field for the whole request: a scanned or chosen device goes to the open line
 * it fits. Typing lists matching devices from the pool; a scanner works anywhere on the page
 * while the field is shown.
 */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const emit = defineEmits<{
  updated: [assetRequest: Schemas['AssetRequestOut'], added: Schemas['AllocationOut'] | null]
}>()
const { t } = useI18n()
const { busy, run } = useAction()

const code = ref('')
const matches = ref<Schemas['LineCandidateOut'][]>([])
const searching = ref(false)
/** What the hits are for; "nothing found" only shows once a search has answered. */
const searched = ref('')
const field = ref<HTMLElement | null>(null)
/** The device just added and where it went, shown below the field. */
const placed = ref('')

const lineOf = (id: Id) => props.assetRequest.items.find((i) => i.id === id)

const options = () =>
  matches.value.map((m) => ({
    value: m.asset.id,
    label: `${m.asset.inventory_number} · ${m.asset.model.full_name}`,
  }))

/** A hit reads like the rows below: icon, device, and the line it would go to. */
function renderLabel(option: { value?: string | number }) {
  const match = matches.value.find((m) => m.asset.id === option.value)
  if (!match) return null
  const line = lineOf(match.item)
  return h('span', { class: 'hit' }, [
    h(categoryIcon(line?.category_icon), { size: 15, class: 'muted' }),
    h('span', { class: 'mono' }, match.asset.inventory_number),
    h('span', { class: 'text' }, [
      match.asset.model.full_name,
      match.asset.serial_number ? ` · ${match.asset.serial_number}` : '',
    ]),
    line ? h('span', { class: 'muted target' }, `→ ${itemLabel(line)}`) : null,
  ])
}

let latest = 0
async function search(q: string) {
  const call = ++latest
  searched.value = ''
  if (!q) {
    matches.value = []
    return
  }
  searching.value = true
  try {
    const result = await requestsApi.lineCandidates(props.assetRequest.id, q)
    if (call === latest) {
      matches.value = result.matches
      searched.value = q
    }
  } catch {
    // The list only helps; scanning the code still works.
  } finally {
    if (call === latest) searching.value = false
  }
}

async function allocate(data: Partial<Schemas['ScanIn']>) {
  const before = new Set(props.assetRequest.items.flatMap((i) => i.allocations.map((a) => a.id)))
  const updated = await run(() => requestsApi.scan(props.assetRequest.id, data))
  if (!updated) return
  code.value = ''
  matches.value = []
  searched.value = ''
  let added: Schemas['AllocationOut'] | null = null
  for (const item of updated.items) {
    const found = item.allocations.find((a) => !before.has(a.id))
    if (found) {
      added = found
      placed.value = t('requests.preparation.placed', {
        number: found.asset?.inventory_number ?? '',
        line: itemLabel(item),
      })
    }
  }
  emit('updated', updated, added)
}

/** A scan outside the field: errors then point at the field, as for a scan into it. */
useScanner((scanned) => {
  field.value?.querySelector('input')?.focus()
  void allocate({ code: scanned })
})
</script>

<template>
  <div ref="field" class="scan-field">
    <ScanCombobox
      v-model="code"
      :options="options()"
      :render-label="renderLabel"
      :placeholder="t('requests.preparation.scan')"
      :loading="searching || busy"
      :empty-text="searched && !searching ? t('requests.allocation.noCandidates') : undefined"
      @search="search"
      @select="(id) => allocate({ asset: id })"
      @enter="(scanned) => allocate({ code: scanned })"
    />
    <div v-if="placed" class="placed" role="status">{{ placed }}</div>
  </div>
</template>

<style scoped>
.scan-field {
  display: grid;
  gap: 6px;
}
.placed {
  color: var(--ar-success);
  font-size: 12px;
}
:global(.hit) {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
:global(.hit .mono) {
  font-family: var(--ar-font-mono);
  font-size: 12px;
}
:global(.hit .target) {
  margin-left: auto;
  font-size: 12px;
  white-space: nowrap;
}
</style>
