import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import DateField from '@/components/common/DateField.vue'
import RequestPeriodCard from '@/components/requests/request/RequestPeriodCard.vue'
import { periodQuery, type RequestPeriod } from '@/components/requests/request/types'
import { fromIsoDate } from '@/composables/useFormat'
import { i18n } from '@/i18n'

const day = (iso: string) => fromIsoDate(iso)!
const mounted: { unmount: () => void }[] = []

/** The card edits the period in place, as the new-request page shares it with the cart. */
function mountCard() {
  const period = reactive<RequestPeriod>({
    duration: 'temporary',
    range: [day('2026-10-12'), day('2026-10-16')],
    start: day('2026-10-12'),
    pickup: day('2026-10-12'),
  })
  const wrapper = mount(RequestPeriodCard, {
    props: { modelValue: period, showsAvailability: false },
    attachTo: document.body,
    global: { plugins: [i18n] },
  })
  mounted.push(wrapper)
  // The date pickers are Naive UI popups; the employee's choice arrives as their update event.
  const pickupField = () => wrapper.findAllComponents(DateField).at(-1)!
  async function choosePickup(iso: string) {
    pickupField().vm.$emit('update:value', day(iso))
    await flushPromises()
  }
  return { period, wrapper, choosePickup }
}

describe('RequestPeriodCard', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 12, 10, 0))
  })
  afterEach(() => {
    mounted.splice(0).forEach((wrapper) => wrapper.unmount())
    document.body.innerHTML = ''
    vi.useRealTimers()
  })

  it('moves the pickup day with the first day until the employee picks one', async () => {
    const { period } = mountCard()
    period.range = [day('2026-10-19'), day('2026-10-23')]
    await flushPromises()
    expect(period.pickup).toBe(day('2026-10-19'))
  })

  it('keeps an earlier pickup day the employee chose', async () => {
    const { period, choosePickup } = mountCard()
    period.range = [day('2026-10-19'), day('2026-10-23')]
    await flushPromises()
    await choosePickup('2026-10-16')
    period.range = [day('2026-10-26'), day('2026-10-30')]
    await flushPromises()
    expect(period.pickup).toBe(day('2026-10-16'))
    // Asked for from the pickup day on: the devices leave then.
    expect(periodQuery(period)).toEqual({ start: '2026-10-16', end: '2026-10-30' })
  })

  it('never keeps the pickup after the devices are needed', async () => {
    const { period, choosePickup } = mountCard()
    period.range = [day('2026-10-19'), day('2026-10-23')]
    await flushPromises()
    await choosePickup('2026-10-16')
    period.range = [day('2026-10-14'), day('2026-10-15')]
    await flushPromises()
    expect(period.pickup).toBe(day('2026-10-14'))
  })

  it('follows the start date of a permanent request', async () => {
    const { period, wrapper } = mountCard()
    await wrapper.find('input[value="permanent"]').setValue(true)
    expect(period.duration).toBe('permanent')
    expect(wrapper.text()).toContain('Needed from')
    period.start = day('2026-11-02')
    await flushPromises()
    expect(period.pickup).toBe(day('2026-11-02'))
    expect(periodQuery(period)).toEqual({ start: '2026-11-02', permanent: true })
  })

  it('offers pickup days from today up to the first day only', () => {
    const { wrapper } = mountCard()
    const pickupField = wrapper.findAllComponents(DateField).at(-1)!
    const isDisabled = pickupField.vm.$attrs['is-date-disabled'] as (ts: number) => boolean
    expect(isDisabled(day('2026-10-11'))).toBe(true)
    expect(isDisabled(day('2026-10-12'))).toBe(false)
    expect(isDisabled(day('2026-10-13'))).toBe(true)
  })
})
