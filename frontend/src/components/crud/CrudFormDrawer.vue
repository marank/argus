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
import { computed, h, nextTick, reactive, watch, type Component } from 'vue'
import { useI18n } from 'vue-i18n'

import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import FormSection from '@/components/common/FormSection.vue'
import ToggleRow from '@/components/common/ToggleRow.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFieldErrors } from '@/composables/useFieldErrors'
import { useFormat } from '@/composables/useFormat'
import { CATEGORY_ICONS } from '@/utils/icons'

import { helpKey, isFieldVisible, sectionFields, type FieldDef, type ResourceDef } from './types'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{
  resource: ResourceDef<any>
  row: any | null
  readonly?: boolean
  /** For a new record: the record it builds on (see `derive` of the resource). */
  source?: any | null
}>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()
const confirm = useConfirm()

const form = reactive<Record<string, any>>({})
const fieldErrors = useFieldErrors(form)
/** Labels of entity values set by the form itself (taken over from another record). */
const labels = reactive<Record<string, any>>({})

const fieldsByKey = computed(() => new Map(sectionFields(props.resource).map((f) => [f.key, f])))

/** The record(s) an entity field shows for its value. */
function initialOf(field: FieldDef & { type: 'entity' }) {
  if (field.key in labels) return labels[field.key]
  return props.row && field.initial ? field.initial(props.row) : null
}

/** Takes over the `copy` fields of `source`; lists are merged with what the form has. */
function takeOver(source: any) {
  const derive = props.resource.derive!
  const values = props.resource.toForm(source)
  for (const key of derive.copy) {
    const field = fieldsByKey.value.get(key)
    const label = field?.type === 'entity' && field.initial ? field.initial(source) : undefined
    if (Array.isArray(values[key])) {
      const own: any[] = Array.isArray(form[key]) ? form[key] : []
      const ownLabels = field?.type === 'entity' ? (initialOf(field) ?? []) : []
      form[key] = [...new Set([...own, ...(values[key] as any[])])]
      if (label) labels[key] = [...ownLabels, ...label]
    } else {
      form[key] = values[key]
      if (label) labels[key] = label
    }
  }
}

function resetForm() {
  for (const key of Object.keys(form)) delete form[key]
  for (const key of Object.keys(labels)) delete labels[key]
  fieldErrors.clear()
  Object.assign(form, props.row ? props.resource.toForm(props.row) : props.resource.defaults())
  const derive = props.resource.derive
  if (!props.row && props.source && derive) {
    takeOver(props.source)
    form[derive.link] = props.source.id
    labels[derive.link] = props.source
  }
}

/** Choosing the record to build on offers to take over its fields. */
async function onSelect(field: FieldDef, item: any) {
  const derive = props.resource.derive
  if (!derive || field.key !== derive.link || !item || item.id === props.row?.id) return
  labels[derive.link] = item
  const names = derive.copy
    .map((key) => fieldsByKey.value.get(key))
    .filter((f) => f && isFieldVisible(f, form))
    .map((f) => t(f!.label))
  const take = await confirm(
    t('masterdata.takeOver', { name: props.resource.title(item), fields: names.join(', ') }),
    { positiveText: t('masterdata.takeOverYes'), negativeText: t('masterdata.takeOverNo') },
  )
  if (take) takeOver(item)
}

watch(show, (visible) => {
  if (visible) resetForm()
})

const title = computed(() =>
  props.row
    ? `${t(`masterdata.singular.${props.resource.key}`)} · ${props.resource.title(props.row)}`
    : `${t(`masterdata.singular.${props.resource.key}`)} · ${t('common.create')}`,
)

const iconOptions = (field: { icons?: Record<string, Component>; group?: string }) =>
  Object.entries(field.icons ?? CATEGORY_ICONS).map(([name, icon]) => ({
    value: name,
    label: field.group ? enumLabel(field.group, name) : name,
    icon,
  }))
const renderIconLabel = (option: { label: string; icon: any }) =>
  h('span', { class: 'row' }, [h(option.icon, { size: 15 }), option.label])

// Only what is shown counts: a required field hidden by another choice (or in a hidden
// section) is not asked for and must not block saving.
const missingRequired = computed(() =>
  props.resource.sections
    .filter((section) => section.visible?.(form) ?? true)
    .flatMap((section) => section.fields)
    .some(
      (f) =>
        f.required &&
        isFieldVisible(f, form) &&
        (form[f.key] === null || form[f.key] === '' || form[f.key] === undefined),
    ),
)

function span(field: FieldDef): number {
  if (field.span) return field.span
  if (field.type === 'textarea') return 2
  if (field.type === 'entity' && field.multiple) return 2
  return 1
}

/** Saves; with `another` (new records only) the drawer stays open with an empty form for the next one. */
async function save(another = false) {
  fieldErrors.clear()
  const ok = await run(() =>
    (props.row
      ? props.resource.api.update(props.row.id, { ...form })
      : props.resource.api.create({ ...form })
    ).catch(fieldErrors.capture),
  )
  if (!ok) return
  emit('saved')
  if (another && !props.row) {
    resetForm()
    await nextTick()
    document.querySelector<HTMLInputElement>('.ar-form input')?.focus()
  } else {
    show.value = false
  }
}
</script>

<template>
  <NDrawer v-model:show="show" :width="600">
    <NDrawerContent :title="title" closable>
      <NForm
        class="ar-form"
        label-placement="top"
        size="medium"
        :show-feedback="false"
        :disabled="readonly"
        @submit.prevent="save()"
      >
        <template v-for="(section, index) in resource.sections" :key="section.title ?? index">
          <FormSection
            v-if="section.visible?.(form) ?? true"
            :title="section.title ? t(section.title) : undefined"
            :class="{ 'toggles-first': section.togglesFirst }"
          >
            <NGrid class="grid" :cols="2" :x-gap="12">
              <NFormItemGi
                v-for="field in section.fields.filter(
                  (f) => f.type !== 'switch' && isFieldVisible(f, form),
                )"
                :key="field.key"
                :span="span(field)"
                v-bind="fieldErrors.item(field.key)"
              >
                <template #label>
                  <FieldLabel
                    :label="t(field.label)"
                    :required="field.required"
                    :help="helpKey(field) ? t(helpKey(field)!) : undefined"
                  />
                </template>
                <NInput
                  v-if="field.type === 'text'"
                  v-model:value="form[field.key]"
                  :disabled="!!row && !!field.locked?.(row)"
                />
                <NInput
                  v-else-if="field.type === 'mono'"
                  v-model:value="form[field.key]"
                  class="mono-input"
                  :disabled="!!row && !!field.locked?.(row)"
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
                  :options="
                    field.values.map((v) => ({ value: v, label: enumLabel(field.group, v) }))
                  "
                />
                <NSelect
                  v-else-if="field.type === 'icon'"
                  v-model:value="form[field.key]"
                  :options="iconOptions(field)"
                  :render-label="renderIconLabel as never"
                  :clearable="!field.required"
                />
                <EntitySelect
                  v-else-if="field.type === 'entity'"
                  v-model="form[field.key]"
                  :fetcher="field.fetcher"
                  :label="field.display"
                  :params="field.params"
                  :multiple="field.multiple"
                  :initial="initialOf(field)"
                  @select="(item: any) => onSelect(field, item)"
                />
              </NFormItemGi>
            </NGrid>
            <!-- Switches as a list below the inputs: label and explanation left, switch right. -->
            <div
              v-if="section.fields.some((f) => f.type === 'switch' && isFieldVisible(f, form))"
              class="toggles"
            >
              <ToggleRow
                v-for="field in section.fields.filter(
                  (f) => f.type === 'switch' && isFieldVisible(f, form),
                )"
                :key="field.key"
                v-model="form[field.key]"
                :label="t(field.label)"
                :help="helpKey(field) ? t(helpKey(field)!) : undefined"
                :error="fieldErrors.errors[field.key]"
                :disabled="readonly"
              />
            </div>
            <component
              :is="section.extra"
              v-if="section.extra"
              :form="form"
              :row="row"
              :readonly="readonly"
              @set="(key: string, value: unknown) => (form[key] = value)"
            />
          </FormSection>
        </template>
      </NForm>
      <template #footer>
        <div class="row">
          <NButton @click="show = false">{{
            readonly ? t('common.close') : t('common.cancel')
          }}</NButton>
          <NButton
            v-if="!readonly && !row"
            :loading="busy"
            :disabled="missingRequired"
            @click="save(true)"
            >{{ t('common.createAndNew') }}</NButton
          >
          <NButton
            v-if="!readonly"
            type="primary"
            :loading="busy"
            :disabled="missingRequired"
            @click="save()"
            >{{ t('common.save') }}</NButton
          >
        </div>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
.toggles {
  display: grid;
}
.form-section:not(.toggles-first) .grid:has(.n-form-item) + .toggles {
  margin-top: 6px;
  border-top: 1px solid var(--ar-border);
}
/* Switches first, then the inputs they reveal, indented below them. */
.toggles-first .toggles {
  order: -1;
}
.toggles-first .grid:has(.n-form-item) {
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px solid var(--ar-primary-soft);
}
</style>
