<script setup lang="ts">
import {
  ArrowLeftRight,
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  ScanLine,
  X,
} from '@lucide/vue'
import { NAlert, NButton, NDrawer, NSkeleton, useMessage } from 'naive-ui'
import { useEventListener, useMediaQuery, watchDebounced } from '@vueuse/core'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'

import { assetsApi } from '@/api/inventory'
import { portalApi, requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import CatalogBrowser from '@/components/requests/request/CatalogBrowser.vue'
import ConsumableQuickPick from '@/components/requests/request/ConsumableQuickPick.vue'
import DirectPicker from '@/components/requests/request/DirectPicker.vue'
import RequestCartPanel from '@/components/requests/request/RequestCartPanel.vue'
import RequestPeriodCard from '@/components/requests/request/RequestPeriodCard.vue'
import RequestPurposeCard from '@/components/requests/request/RequestPurposeCard.vue'
import {
  fittingDevices,
  optionKey,
  periodQuery,
  requestInput,
  type CartLine,
  type RequestDetails,
  type RequestPeriod,
} from '@/components/requests/request/types'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { scrollerOf } from '@/utils/scroll'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import { useAuthStore } from '@/stores/auth'
import { anyModelLabel, itemLabel } from '@/utils/requests'
import { useFeaturesStore } from '@/stores/features'

const { t } = useI18n()
const features = useFeaturesStore()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const { busy, run } = useAction()
const { date } = useFormat()

/**
 * IT staff first choose between a request and a direct hand-out of specific
 * devices from stock (`?mode=direct`); everyone else only requests.
 * `?from=<id>` asks again for an earlier request: a request, prefilled.
 */
const canDirect = computed(() => auth.can('requests', 'write'))
const mode = computed<'request' | 'direct' | null>(() => {
  if (!canDirect.value || route.query.from) return 'request'
  const value = route.query.mode
  return value === 'direct' || value === 'request' ? value : null
})
const direct = computed(() => mode.value === 'direct')

const choices = computed(() => [
  {
    mode: 'request' as const,
    icon: ClipboardList,
    title: t('requests.direct.chooseRequest'),
    hint: t('requests.direct.chooseRequestHint'),
    points: [
      t('requests.direct.requestPoints.catalog'),
      t('requests.direct.requestPoints.approval'),
      t('requests.direct.requestPoints.confirm'),
    ],
  },
  {
    mode: 'direct' as const,
    icon: ScanLine,
    title: t('requests.direct.title'),
    hint: t('requests.direct.chooseDirectHint'),
    points: [
      t('requests.direct.directPoints.scan'),
      t('requests.direct.directPoints.noApproval'),
      t('requests.direct.directPoints.protocol'),
    ],
  },
])

function choose(value: 'request' | 'direct' | null) {
  // A device from the device page stays picked whichever way is chosen.
  const asset = route.query.asset ? { asset: route.query.asset } : {}
  router.replace({ query: value ? { mode: value, ...asset } : asset })
}

const catalog = ref<Schemas['CatalogCategoryOut'][] | null>(null)
const cart = ref<CartLine[]>([])
const myConsumables = ref<Schemas['MyConsumablesOut'][]>([])

const today = new Date().setHours(0, 0, 0, 0)
const period = reactive<RequestPeriod>({
  duration: 'temporary',
  // Suggested period from the site settings (default loan period, start day included).
  range: [today, today + (features.rules.default_loan_days - 1) * 86400000],
  start: today,
  pickup: today,
})

// The two modes fill the cart differently; switching starts over.
watch(direct, () => (cart.value = []))

onMounted(async () => {
  // The quick pick can be switched off; its endpoint is gone then.
  const [entries, consumables] = await Promise.all([
    portalApi.catalog(periodQuery(period)),
    features.isOn('consumable_quick_pick') ? portalApi.myConsumables() : Promise.resolve([]),
  ])
  catalog.value = entries
  myConsumables.value = consumables
  if (typeof route.query.from === 'string') {
    const earlier = await run(() => requestsApi.get(route.query.from as string))
    if (earlier) prefill(earlier)
  }
})

/** Purpose, for whom, and the message to IT; sent with period and cart. */
const details = reactive<RequestDetails>({ title: '', notes: '', requester: null })
/** Shown in the person picker before its list loads, when asking again for someone else. */
const initialRequester = ref<Schemas['UserRefOut'] | null>(null)

/** Asking again: the earlier request's lines, details and period (moved to today if past). */
const previous = ref<Schemas['AssetRequestOut'] | null>(null)

function prefill(earlier: Schemas['AssetRequestOut']) {
  previous.value = earlier
  let freeText = 0
  cart.value = earlier.items.map((item) => {
    const key = item.description
      ? `f${++freeText}`
      : item.asset_model
        ? `m${item.asset_model.id}`
        : `c${item.category!.id}`
    return {
      key,
      label: itemLabel(item),
      category: item.asset_model ? undefined : item.category?.id,
      asset_model: item.asset_model?.id,
      description: item.description || undefined,
      quantity: item.quantity_requested,
      note: item.note,
      available: availableFor(key),
    }
  })
  const start = fromIsoDate(earlier.start_date)!
  const end = fromIsoDate(earlier.end_date) ?? start
  const first = Math.max(start, today)
  period.duration = earlier.duration
  period.start = first
  period.range = [first, first + Math.max(end - start, 0)]
  period.pickup = first
  // Recorded for someone else: keep them as the requester.
  initialRequester.value = earlier.requester.id === auth.user?.id ? null : earlier.requester
  Object.assign(details, {
    title: earlier.title,
    notes: earlier.notes,
    requester: initialRequester.value?.id ?? null,
  })
}

// From the device page: hand out that device, or request its model.
watch(
  [mode, () => route.query.asset, catalog],
  async ([current, id, entries]) => {
    if (typeof id !== 'string' || !current || (current === 'request' && !entries)) return
    const asset = await run(() => assetsApi.get(id))
    if (!asset) return
    if (current === 'direct') addAsset(asset)
    else addModelOf(asset)
  },
  { immediate: true },
)

function addModelOf(asset: Schemas['AssetOut']) {
  for (const category of catalog.value ?? []) {
    const model = category.models.find((m) => m.id === asset.model.id)
    if (!model) continue
    if (!cart.value.some((line) => line.key === optionKey(category, model))) add(category, model)
    return
  }
}

/** Lookup of what is free in the period, by cart/option key. */
function availableFor(key: string): number | null {
  for (const category of catalog.value ?? []) {
    if (key === optionKey(category)) return category.available
    const model = category.models.find((m) => key === optionKey(category, m))
    if (model) return model.available
  }
  return null
}

// IT handling requests sees availability for the chosen period: refresh the counts when it changes.
let latestQuery = 0
watchDebounced(
  () => periodQuery(period),
  async (query) => {
    if (!auth.can('requests') || !catalog.value || direct.value) return
    const current = ++latestQuery
    const counts = await portalApi.availability(query)
    if (current !== latestQuery) return // a newer period was chosen meanwhile
    for (const category of catalog.value) {
      Object.assign(category, counts.categories[category.id] ?? { available: 0, reserved: 0 })
      for (const model of category.models) {
        Object.assign(model, counts.models[model.id] ?? { available: 0, reserved: 0 })
      }
    }
    for (const line of cart.value) line.available = availableFor(line.key)
  },
  { debounce: 250 },
)

/** How many of the employee's devices have something in the catalog that fits them. */
const fitting = computed(() =>
  catalog.value ? fittingDevices(myConsumables.value, catalog.value).length : 0,
)

const cartCounts = computed(() =>
  Object.fromEntries(cart.value.map((line) => [line.key, line.quantity])),
)

function add(category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']) {
  const key = optionKey(category, model)
  const existing = cart.value.find((line) => line.key === key)
  if (existing) {
    existing.quantity += 1
    return
  }
  cart.value.push({
    key,
    label: model ? model.full_name : anyModelLabel(category),
    category: model ? undefined : category.id,
    asset_model: model?.id,
    quantity: 1,
    note: '',
    available: model ? model.available : category.available,
  })
}

/** The minus of an option's stepper: one less, and gone at none. */
function remove(category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']) {
  const index = cart.value.findIndex((line) => line.key === optionKey(category, model))
  if (index < 0) return
  if (cart.value[index]!.quantity > 1) cart.value[index]!.quantity -= 1
  else cart.value.splice(index, 1)
}

function addAsset(asset: Schemas['AssetOut']) {
  const key = `a${asset.id}`
  if (cart.value.some((line) => line.key === key)) return
  cart.value.push({
    key,
    label: asset.model.full_name,
    code: asset.inventory_number,
    asset: asset.id,
    quantity: 1,
    note: '',
    available: null,
  })
}

function addConsumable(consumable: Schemas['ConsumableOut']) {
  const key = `s${consumable.id}`
  const existing = cart.value.find((line) => line.key === key)
  if (existing) {
    existing.quantity = Math.min(existing.quantity + 1, consumable.available_quantity)
    return
  }
  cart.value.push({
    key,
    label: consumable.model.full_name,
    consumable: consumable.id,
    quantity: 1,
    max: consumable.available_quantity,
    note: '',
    available: null,
  })
}

let freeTextCounter = 0

function addFreeText(text: string, category?: Schemas['CatalogCategoryOut']) {
  cart.value.push({
    key: `f${++freeTextCounter}`,
    label: category ? `${category.name}: ${text}` : text,
    category: category?.id,
    description: text,
    quantity: 1,
    note: '',
    available: null,
  })
}

/** In a direct hand-out the cart holds devices and stocks instead of catalog lines. */
function directInput(data: Schemas['AssetRequestIn']): Schemas['DirectRequestIn'] {
  const { items, ...fields } = data
  void items
  return {
    ...fields,
    assets: cart.value.flatMap((line) => (line.asset ? [line.asset] : [])),
    consumables: cart.value.flatMap((line) =>
      line.consumable ? [{ consumable: line.consumable, quantity: line.quantity }] : [],
    ),
  }
}

async function submit() {
  if (!cart.value.length || needsPurpose()) return
  const data = requestInput(period, details, cart.value)
  const assetRequest = await run(() =>
    direct.value
      ? requestsApi.createDirect(directInput(data))
      : requestsApi.create({ ...data, follows: previous.value?.id ?? null }),
  )
  if (!assetRequest) return
  submitted.value = true
  // IT continues on the request itself; employees follow it in the portal.
  if (auth.can('requests')) {
    message.success(t('requests.new.submitted', { number: assetRequest.number }))
    router.push({ name: 'request', params: { id: assetRequest.id } })
  } else {
    router.push({
      name: 'portal-request',
      params: { id: assetRequest.id },
      query: { created: '1' },
    })
  }
}

/**
 * Two steps: details (period and purpose), then the selection. The cart is a panel like a
 * form drawer, with the send button at its foot: docked right of the catalog where there
 * is room, a drawer from the right where not, a sheet from below on a phone. A phone shows
 * the selection as a menu (groups, then one group) and has its buttons at the thumb.
 */
type Step = 'period' | 'catalog'
const STEPS: Step[] = ['period', 'catalog']
const narrow = useMediaQuery('(max-width: 760px)')
/** Too narrow for catalog and cart side by side. */
const cramped = useMediaQuery('(max-width: 1099px)')
const step = ref<Step>('period')
/**
 * The selection is an entry of its own in the browser's history: back (a phone's back
 * gesture too) leads to the details instead of out of the request. Reloaded on it, the
 * details are gone, so the page starts on them again.
 */
if (route.query.step) router.replace({ query: { ...route.query, step: undefined } })
watch(
  () => route.query.step,
  (value) => go(value === 'catalog' ? 'catalog' : 'period'),
)
/** Where the page was opened from, to return there on cancel (none when opened directly). */
const cameFrom = !!window.history.state?.back
const catalogOpened = ref(false)
const cartOpen = ref(false)
watch(cramped, (isCramped) => isCramped || (cartOpen.value = false))
const cartTotal = computed(() => cart.value.reduce((sum, line) => sum + line.quantity, 0))

const head = ref<HTMLElement | null>(null)
const catalogPanel = ref<{ selectedName: string } | null>(null)
const purposeCard = ref<{ focus: () => void } | null>(null)

/** A step comes in from the side it lies on and starts at the top. */
const motion = ref<'ar-forward' | 'ar-back'>('ar-forward')
function go(next: Step) {
  if (next === step.value) return
  motion.value = STEPS.indexOf(next) > STEPS.indexOf(step.value) ? 'ar-forward' : 'ar-back'
  step.value = next
  nextTick(() => scrollerOf(head.value)?.scrollTo?.({ top: 0 }))
}

/** On a phone an open group sits between: back leads to all groups first. */
const groupOpen = computed(() => narrow.value && step.value === 'catalog' && catalogOpened.value)

/** One step back (from a phone's bar): out of the open group first. */
function back() {
  // The catalog keeps the list of groups where it was.
  if (groupOpen.value) catalogOpened.value = false
  else toDetails()
}

/** Back to the details: the selection's history entry is left, as with the browser's back. */
function toDetails() {
  if (route.query.step === 'catalog') router.back()
}

/** Set when going on was tried without a purpose: the field says so then. */
const purposeMissing = ref(false)
/** Without a purpose: back to it, marked and with the cursor in it, instead of a dead button. */
function needsPurpose(): boolean {
  if (details.title.trim()) return false
  purposeMissing.value = true
  cartOpen.value = false
  toDetails()
  nextTick(() => purposeCard.value?.focus())
  return true
}

function toCatalog() {
  if (needsPurpose()) return
  catalogOpened.value = false
  if (route.query.step !== 'catalog') router.push({ query: { ...route.query, step: 'catalog' } })
}

/** Back to the details from the cart panel. */
function editDetails() {
  cartOpen.value = false
  toDetails()
}

const stepTitle = computed(() =>
  groupOpen.value
    ? (catalogPanel.value?.selectedName ?? '')
    : t(`requests.new.steps.${step.value}`),
)
/** The period as the cart panel repeats it: from and to, or from on for good. */
const periodText = computed(() =>
  period.duration === 'permanent'
    ? `${date(toIsoDate(period.start))} → ${t('common.permanent')}`
    : `${date(toIsoDate(period.range[0]))} → ${date(toIsoDate(period.range[1]))}`,
)
/** What the panel repeats from the first step, once that step is done. */
const cartDetails = computed(() =>
  step.value === 'catalog'
    ? { period: periodText.value, purpose: details.title.trim() }
    : undefined,
)

/** Something to lose: leaving the page asks first (also reloading or closing the tab). */
const submitted = ref(false)
/** Set once the person chose to throw it away: leaving then asks no more. */
const discarded = ref(false)
const dirty = computed(
  () => !submitted.value && !discarded.value && (cart.value.length > 0 || !!details.title.trim()),
)
const confirm = useConfirm()
/** One question wherever the request would be lost: the X, the menu, the browser's back. */
const confirmDiscard = () =>
  confirm(t('requests.new.cancelConfirm'), {
    danger: true,
    positiveText: t('requests.new.cancelDiscard'),
    negativeText: t('requests.new.leaveStay'),
  })
/** Back with the cart open (a phone's back gesture) closes the cart first. */
function closesCart(): boolean {
  if (!cartOpen.value) return false
  cartOpen.value = false
  return true
}
onBeforeRouteLeave(() => {
  if (closesCart()) return false
  return dirty.value ? confirmDiscard() : true
})
onBeforeRouteUpdate((to, from) => {
  // Switching between request and direct hand-out starts over as well.
  if (to.query.mode !== from.query.mode) return dirty.value ? confirmDiscard() : true
  return to.query.step === from.query.step || !closesCart()
})
/**
 * The X in the header: leave the request, back where one came from (or to the dashboard
 * when the page was opened directly). With something entered it asks first, once.
 */
async function cancel() {
  if (dirty.value) {
    if (!(await confirmDiscard())) return
    discarded.value = true
  }
  // On the selection its own history entry lies in between.
  if (cameFrom) router.go(route.query.step === 'catalog' ? -2 : -1)
  else router.push({ name: 'dashboard' })
}

useEventListener(window, 'beforeunload', (event: BeforeUnloadEvent) => {
  if (dirty.value) event.preventDefault()
})

const header = computed(() =>
  direct.value
    ? { title: t('requests.direct.title'), subtitle: t('requests.direct.subtitle') }
    : { title: t('requests.new.title'), subtitle: t('requests.new.subtitle') },
)
</script>

<template>
  <div class="page" :class="{ flow: mode !== null }">
    <template v-if="mode === null">
      <PageHeader :title="t('requests.new.title')" :subtitle="t('requests.direct.choose')" />
      <div class="choices">
        <button
          v-for="choice in choices"
          :key="choice.mode"
          type="button"
          class="choice"
          :class="choice.mode"
          @click="choose(choice.mode)"
        >
          <span class="choice-head">
            <span class="choice-icon"
              ><component :is="choice.icon" :size="22" :stroke-width="1.6"
            /></span>
            <ArrowRight class="go" :size="18" />
          </span>
          <strong>{{ choice.title }}</strong>
          <span class="muted">{{ choice.hint }}</span>
          <ul class="points">
            <li v-for="point in choice.points" :key="point">
              <Check :size="14" :stroke-width="2.2" />{{ point }}
            </li>
          </ul>
        </button>
      </div>
    </template>

    <template v-else>
      <!-- Where one is and the ways out; the cart where it is not docked. -->
      <header ref="head" class="wizard-head">
        <div class="head-titles">
          <span v-if="narrow" class="eyebrow">{{
            t('requests.new.steps.ofShort', { n: STEPS.indexOf(step) + 1, total: STEPS.length })
          }}</span>
          <!-- The steps as a trail: the first one stays one click away. -->
          <nav v-else class="eyebrow crumbs" :aria-label="header.title">
            <span>{{ header.title }}</span>
            <template v-for="(s, index) in STEPS" :key="s">
              <ChevronRight :size="12" />
              <button
                type="button"
                class="crumb"
                :class="{ active: s === step }"
                :aria-current="s === step ? 'step' : undefined"
                @click="s === 'period' ? editDetails() : toCatalog()"
              >
                {{ index + 1 }} · {{ t(`requests.new.steps.${s}`) }}
              </button>
            </template>
          </nav>
          <Transition name="ar-fade" mode="out-in">
            <strong :key="stepTitle" class="head-title">{{ stepTitle }}</strong>
          </Transition>
        </div>
        <span class="head-side end">
          <!-- Docked, the selection has no bar below: back to the details up here. -->
          <NButton v-if="!cramped && step === 'catalog'" class="head-back" @click="toDetails">
            <template #icon><ChevronLeft :size="16" /></template>
            {{ t('common.back') }}
          </NButton>
          <NButton
            v-if="canDirect"
            quaternary
            circle
            :title="t('requests.direct.switch')"
            @click="choose(null)"
          >
            <template #icon><ArrowLeftRight :size="16" /></template>
          </NButton>
          <!-- Leaves the request; asks first when something would be lost. -->
          <NButton
            quaternary
            circle
            class="close-button"
            :title="t('requests.new.cancel')"
            :aria-label="t('requests.new.cancel')"
            @click="cancel"
          >
            <template #icon><X :size="20" /></template>
          </NButton>
        </span>
      </header>
      <NAlert v-if="previous" type="info" :bordered="false" class="again">
        {{ t('requests.again.prefilled', { number: previous.number }) }}
      </NAlert>

      <div class="steps-body" :class="{ docked: !cramped }">
        <div class="steps-main">
          <!-- 1 · Period and purpose, with the way on right below the fields -->
          <Transition :name="motion">
            <div v-show="step === 'period'" class="step-panel first-step">
              <section class="details-card">
                <header>
                  <ClipboardList :size="16" />
                  <h2>{{ t('requests.new.steps.period') }}</h2>
                </header>
                <!-- What for first: that is what people think of, before dates. -->
                <RequestPurposeCard
                  ref="purposeCard"
                  v-model="details"
                  plain
                  :missing="purposeMissing"
                  :can-choose-requester="canDirect"
                  :requester-placeholder="auth.user?.display_name"
                  :initial-requester="initialRequester"
                  @enter="toCatalog"
                />
                <RequestPeriodCard
                  v-model="period"
                  plain
                  :shows-availability="auth.can('requests')"
                />
                <footer class="details-foot">
                  <NButton
                    type="primary"
                    icon-placement="right"
                    class="next-button"
                    @click="toCatalog"
                  >
                    {{ t('requests.new.steps.to.catalog') }}
                    <template #icon><ArrowRight :size="16" /></template>
                  </NButton>
                </footer>
              </section>
            </div>
          </Transition>

          <!-- 2 · Selection: groups and their content (a menu on a phone) -->
          <Transition :name="motion">
            <div v-show="step === 'catalog'" class="step-panel">
              <NSkeleton v-if="!catalog" height="320px" />
              <CatalogBrowser
                v-else
                ref="catalogPanel"
                v-model:opened="catalogOpened"
                :catalog="catalog"
                :cart-counts="cartCounts"
                :direct="direct"
                :fitting="fitting"
                @add="add"
                @remove="remove"
                @add-free-text="addFreeText"
              >
                <template #fitting>
                  <ConsumableQuickPick
                    :groups="myConsumables"
                    :catalog="catalog"
                    :cart-counts="cartCounts"
                    @add="add"
                    @remove="remove"
                  />
                </template>
                <template #direct="{ category }">
                  <DirectPicker
                    :category="category"
                    :cart-counts="cartCounts"
                    @add-asset="addAsset"
                    @add-consumable="addConsumable"
                  />
                </template>
              </CatalogBrowser>
            </div>
          </Transition>
        </div>

        <!-- Room enough: the cart stays in view next to the catalog. -->
        <aside v-if="!cramped" class="cart-dock">
          <RequestCartPanel
            :key="mode"
            v-model:lines="cart"
            v-model:notes="details.notes"
            :direct="direct"
            :details="cartDetails"
            :busy="busy"
            @submit="submit"
            @edit="editDetails"
          />
        </aside>
      </div>

      <NDrawer
        v-if="cramped"
        v-model:show="cartOpen"
        :placement="narrow ? 'bottom' : 'right'"
        :width="420"
        height="88%"
        class="cart-drawer"
        :class="{ sheet: narrow }"
      >
        <RequestCartPanel
          :key="mode"
          v-model:lines="cart"
          v-model:notes="details.notes"
          :direct="direct"
          :details="cartDetails"
          :busy="busy"
          closable
          @submit="submit"
          @edit="editDetails"
          @close="cartOpen = false"
        />
      </NDrawer>

      <!--
        Without the docked cart the way on must still be in plain sight: one step back, and
        the cart with the send button. At the thumb on a phone.
      -->
      <div v-if="cramped && step === 'catalog'" class="next-bar">
        <NButton class="back-button" @click="back">
          <template #icon><ChevronLeft :size="16" /></template>
          {{ t('common.back') }}
        </NButton>
        <NButton
          :type="cartTotal ? 'primary' : 'default'"
          icon-placement="right"
          class="next-button cart-bar-button"
          @click="cartOpen = true"
        >
          <span v-if="cartTotal" :key="cartTotal" class="cart-count mono">{{ cartTotal }}</span>
          {{ t('requests.new.review') }}
          <template #icon><ArrowRight :size="16" /></template>
        </NButton>
      </div>
    </template>
  </div>
</template>

<style scoped>
.choices {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 400px));
  justify-content: center;
  gap: 16px;
}
.choice {
  --accent: var(--ar-primary);
  position: relative;
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  align-content: start;
  gap: 8px;
  overflow: hidden;
  padding: 22px 24px 20px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: var(--ar-text-muted);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.15s ease;
}
.choice.direct {
  --accent: var(--ar-violet);
}
/* A strip in the mode's colour that fills in on hover. */
.choice::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: var(--accent);
  transform: scaleX(0.18);
  transform-origin: left;
  transition: transform 0.25s ease;
}
.choice:hover,
.choice:focus-visible {
  border-color: color-mix(in srgb, var(--accent) 55%, var(--ar-border));
  box-shadow: 0 6px 20px -12px color-mix(in srgb, var(--accent) 60%, transparent);
  transform: translateY(-1px);
}
.choice:hover::before,
.choice:focus-visible::before {
  transform: scaleX(1);
}
.choice:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.choice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.choice-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  color: var(--accent);
}
.go {
  color: var(--ar-text-subtle);
  transition:
    transform 0.15s ease,
    color 0.15s ease;
}
.choice:hover .go,
.choice:focus-visible .go {
  color: var(--accent);
  transform: translateX(3px);
}
.choice strong {
  color: var(--ar-text);
  font-size: 16px;
  font-weight: 600;
}
.choice .muted {
  line-height: 1.5;
}
.points {
  display: grid;
  gap: 6px;
  margin: 8px 0 0;
  padding: 12px 0 0;
  border-top: 1px dashed var(--ar-border);
  list-style: none;
  font-size: 12.5px;
}
.points li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--ar-text);
}
.points svg {
  flex: none;
  margin-top: 2px;
  color: var(--accent);
}
@media (prefers-reduced-motion: reduce) {
  .choice,
  .choice::before,
  .go {
    transition: none;
  }
}
@media (max-width: 760px) {
  .choices {
    grid-template-columns: 1fr;
  }
}
/*
 * The steps fill the content area: header on top, the step below, the cart docked on the
 * right where there is room. The header stays in view while a long step scrolls.
 */
.page.flow {
  /* What sticks below the header (the catalog's groups) keeps clear of it. */
  --sticky-top: 64px;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--ar-header-height));
  padding-top: 0;
  padding-bottom: 0;
}
/* Stays on top while a step scrolls: where one is and the ways back and out. */
.wizard-head {
  position: sticky;
  top: 0;
  z-index: 5;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid var(--ar-border);
  background: var(--ar-bg);
}
.head-side {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 34px;
}
.head-side.end {
  justify-content: flex-end;
}
.head-back {
  margin-right: 8px;
}
/* A fixed height: while one title fades out and the next in, the header keeps its size. */
.head-titles {
  display: grid;
  grid-template-rows: 16px 24px;
  min-width: 0;
}
/* The steps as a trail; the current one in the accent colour. */
.crumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  white-space: nowrap;
}
.crumbs svg {
  flex: none;
  color: var(--ar-text-subtle);
}
.crumb {
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  cursor: pointer;
}
.crumb:hover {
  color: var(--ar-primary);
}
.crumb.active {
  color: var(--ar-primary);
  cursor: default;
}
.head-title {
  max-width: 100%;
  overflow: hidden;
  line-height: 24px;
  font-size: 17px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cart-count {
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--ar-primary);
  color: var(--ar-on-primary);
  font-size: 11px;
  font-weight: 700;
  /* Re-keyed on every change, so the count pops. */
  animation: ar-pop 0.25s ease-out;
}
.again {
  margin: 14px 0 0;
}
.steps-body {
  flex: 1;
  padding: 18px 0 24px;
}
/* Catalog and cart side by side; the cart keeps to the window while the catalog scrolls. */
.steps-body.docked {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}
.steps-main {
  min-width: 0;
}
.cart-dock {
  position: sticky;
  top: calc(var(--sticky-top) + 16px);
  height: calc(100vh - var(--ar-header-height) - var(--sticky-top) - 40px);
  max-height: 720px;
  overflow: hidden;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.step-panel {
  display: grid;
  gap: 14px;
  align-content: start;
}
/* A form of a handful of fields: as wide as reads well, centred. */
.first-step {
  width: 100%;
  max-width: 560px;
  margin-inline: auto;
}
.details-card {
  display: grid;
  gap: 12px;
  padding: 16px 18px 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.details-card header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ar-text-muted);
}
.details-card h2 {
  margin: 0;
  color: var(--ar-text);
  font-size: 14px;
  font-weight: 600;
}
/* The way on right below the fields, where the eye already is. */
.details-foot {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid var(--ar-border);
}
/* Below the content, in view while it scrolls; clear of a phone's home indicator. */
.next-bar {
  position: sticky;
  bottom: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0 calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--ar-border);
  background: color-mix(in srgb, var(--ar-bg) 92%, transparent);
  backdrop-filter: blur(8px);
}
.back-button {
  height: 42px;
}
.next-button {
  min-width: 200px;
  height: 38px;
}
/* Back on the left, on to sending on the right. */
.next-bar .next-button {
  margin-left: auto;
  height: 42px;
}
.cart-bar-button .cart-count {
  margin-right: 8px;
  background: var(--ar-on-primary);
  color: var(--ar-primary);
}
/* On a phone the cart comes up from below as a sheet (teleported: no scoped attribute). */
:global(.cart-drawer.sheet) {
  border-radius: 12px 12px 0 0;
}
@media (max-width: 760px) {
  .page.flow {
    padding-inline: 16px;
  }
  /* At the thumb: forward takes the width that back leaves. */
  .next-bar .next-button {
    flex: 1;
    min-width: 0;
  }
  .details-foot .next-button {
    width: 100%;
    height: 42px;
  }
}
</style>
