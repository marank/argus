<script setup lang="ts">
import {
  NButton,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItemGi,
  NGrid,
  NInput,
  NInputNumber,
  NSelect,
} from 'naive-ui'
import { computed, h, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EntitySelect from '@/components/common/EntitySelect.vue'
import CheckField from '@/components/common/CheckField.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { CATEGORY_ICONS } from '@/utils/icons'

import { sectionFields, type FieldDef, type ResourceDef } from './types'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{ resource: ResourceDef<any>; row: any | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const form = reactive<Record<string, any>>({})

watch(show, (visible) => {
  if (!visible) return
  for (const key of Object.keys(form)) delete form[key]
  Object.assign(form, props.row ? props.resource.toForm(props.row) : props.resource.defaults())
})

const title = computed(() =>
  props.row
    ? `${t(`masterdata.singular.${props.resource.key}`)} · ${props.resource.title(props.row)}`
    : `${t(`masterdata.singular.${props.resource.key}`)} · ${t('common.create')}`,
)

const iconOptions = Object.entries(CATEGORY_ICONS).map(([name, icon]) => ({
  value: name,
  label: name,
  icon,
}))
const renderIconLabel = (option: { label: string; icon: any }) =>
  h('span', { class: 'row' }, [h(option.icon, { size: 15 }), option.label])

const missingRequired = computed(() =>
  sectionFields(props.resource).some(
    (f) => f.required && (form[f.key] === null || form[f.key] === '' || form[f.key] === undefined),
  ),
)

function span(field: FieldDef): number {
  if (field.span) return field.span
  if (field.type === 'textarea') return 2
  if (field.type === 'entity' && field.multiple) return 2
  return 1
}

async function save() {
  const ok = await run(
    () =>
      props.row
        ? props.resource.api.update(props.row.id, { ...form })
        : props.resource.api.create({ ...form }),
    t('common.saved'),
  )
  if (ok) {
    show.value = false
    emit('saved')
  }
}
</script>

<template>
  <NDrawer v-model:show="show" :width="600">
    <NDrawerContent :title="title" closable>
      <NForm
        class="ar-form"
        label-placement="top"
        size="small"
        :show-feedback="false"
        @submit.prevent="save"
      >
        <section
          v-for="(section, index) in resource.sections"
          :key="section.title ?? index"
          class="section"
        >
          <div v-if="section.title" class="eyebrow section-title">{{ t(section.title) }}</div>
          <NGrid :cols="2" :x-gap="12">
            <NFormItemGi
              v-for="field in section.fields"
              :key="field.key"
              :span="span(field)"
              :show-label="field.type !== 'switch'"
              :class="{ 'switch-item': field.type === 'switch' }"
            >
              <template #label>
                <FieldLabel
                  :label="t(field.label)"
                  :required="field.required"
                  :help="field.help ? t(field.help) : undefined"
                />
              </template>
              <CheckField
                v-if="field.type === 'switch'"
                v-model="form[field.key]"
                :label="t(field.label)"
                :help="field.help ? t(field.help) : undefined"
              />
              <NInput v-else-if="field.type === 'text'" v-model:value="form[field.key]" />
              <NInput
                v-else-if="field.type === 'mono'"
                v-model:value="form[field.key]"
                class="mono-input"
              />
              <NInput
                v-else-if="field.type === 'textarea'"
                v-model:value="form[field.key]"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 8 }"
              />
              <NInputNumber
                v-else-if="field.type === 'number'"
                v-model:value="form[field.key]"
                :min="field.min"
                :max="field.max"
                :precision="field.precision"
                style="width: 100%"
              />
              <NSelect
                v-else-if="field.type === 'enum'"
                v-model:value="form[field.key]"
                :options="field.values.map((v) => ({ value: v, label: enumLabel(field.group, v) }))"
              />
              <NSelect
                v-else-if="field.type === 'icon'"
                v-model:value="form[field.key]"
                :options="iconOptions"
                :render-label="renderIconLabel as never"
                clearable
              />
              <EntitySelect
                v-else-if="field.type === 'entity'"
                v-model="form[field.key]"
                :fetcher="field.fetcher"
                :label="field.display"
                :params="field.params"
                :multiple="field.multiple"
                :initial="row && field.initial ? field.initial(row) : null"
              />
            </NFormItemGi>
          </NGrid>
          <component :is="section.extra" v-if="section.extra" :form="form" />
        </section>
      </NForm>
      <template #footer>
        <div class="row">
          <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="busy" :disabled="missingRequired" @click="save">{{
            t('common.save')
          }}</NButton>
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
.section + .section {
  margin-top: 8px;
  padding-top: 18px;
  border-top: 1px solid var(--ar-border);
}
.section-title {
  margin-bottom: 12px;
}
/* Checkboxes line up with the inputs next to them, not with their labels. */
.switch-item {
  align-self: end;
}
</style>
