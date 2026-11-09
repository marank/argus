import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, reactive } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { useAction } from '@/composables/useAction'
import { useAssigned } from '@/composables/useAssigned'
import { useConfirm } from '@/composables/useConfirm'
import { errorPopover, hideError } from '@/composables/useErrorPopover'
import { useFieldErrors } from '@/composables/useFieldErrors'
import { useFormat } from '@/composables/useFormat'
import { useScanner } from '@/composables/useScanner'
import { i18n } from '@/i18n'

import { withSetup } from './helpers'

const ui = vi.hoisted(() => ({
  success: vi.fn<(content: string) => void>(),
  error: vi.fn<(content: string, options: object) => void>(),
  dialog: {
    warning: vi.fn<(options: object) => void>(),
    error: vi.fn<(options: object) => void>(),
  },
}))

vi.mock('naive-ui', async (importOriginal) => ({
  ...(await importOriginal<typeof import('naive-ui')>()),
  useMessage: () => ({ success: ui.success, error: ui.error }),
  useDialog: () => ui.dialog,
}))

beforeEach(() => {
  hideError()
  ui.success.mockReset()
  ui.error.mockReset()
  ui.dialog.warning.mockReset()
  ui.dialog.error.mockReset()
})

describe('useAction', () => {
  it('returns the result and shows the success message', async () => {
    const { busy, run } = useAction()
    const pending = run(async () => 42, 'Saved.')
    expect(busy.value).toBe(true)
    expect(await pending).toBe(42)
    expect(busy.value).toBe(false)
    expect(ui.success).toHaveBeenCalledWith('Saved.')
  })

  it('shows no success message unless one is given', async () => {
    const { run } = useAction()
    await run(async () => 1)
    expect(ui.success).not.toHaveBeenCalled()
  })

  it('shows the message of an API error and returns undefined', async () => {
    const { busy, run } = useAction()
    const result = await run(async () => {
      throw new ApiError(409, 'Already handed out.')
    }, 'Saved.')
    expect(result).toBeUndefined()
    expect(busy.value).toBe(false)
    expect(ui.success).not.toHaveBeenCalled()
    expect(errorPopover.message).toBe('Already handed out.')
  })

  it('shows other errors as text', async () => {
    const { run } = useAction()
    await run(async () => {
      throw new Error('boom')
    })
    expect(errorPopover.message).toBe('Error: boom')
  })
})

describe('useConfirm', () => {
  type DialogOptions = {
    title: string
    content: string
    positiveText: string
    negativeText: string
    onPositiveClick: () => void
    onNegativeClick: () => void
    onClose: () => void
    onMaskClick: () => void
  }
  const confirm = () => withSetup(() => useConfirm(), [i18n]).result
  const shown = (kind: 'warning' | 'error') => ui.dialog[kind].mock.calls[0]![0] as DialogOptions

  it('resolves true when confirmed', async () => {
    const answer = confirm()('Delete it?')
    const options = shown('warning')
    expect(options).toMatchObject({
      title: 'Please confirm',
      content: 'Delete it?',
      positiveText: 'Confirm',
      negativeText: 'Cancel',
    })
    options.onPositiveClick()
    expect(await answer).toBe(true)
  })

  it.each(['onNegativeClick', 'onClose', 'onMaskClick'] as const)(
    'resolves false on %s',
    async (how) => {
      const answer = confirm()('Delete it?')
      shown('warning')[how]()
      expect(await answer).toBe(false)
    },
  )

  it('uses the error dialog and own button texts for dangerous actions', async () => {
    const answer = confirm()('Delete it?', {
      danger: true,
      positiveText: 'Delete',
      negativeText: 'Keep',
    })
    expect(ui.dialog.warning).not.toHaveBeenCalled()
    const options = shown('error')
    expect(options).toMatchObject({ positiveText: 'Delete', negativeText: 'Keep' })
    options.onPositiveClick()
    expect(await answer).toBe(true)
  })
})

describe('useFieldErrors', () => {
  const failed = (errors: Record<string, string[]>) => new ApiError(400, 'Check the form.', errors)

  it('takes the errors of fields in the form and rethrows', () => {
    const form = reactive({ name: '', email: '' })
    const { errors, capture } = useFieldErrors(form)
    const error = failed({ name: ['Required.', 'Too short.'], other: ['Elsewhere.'], email: [] })
    expect(() => capture(error)).toThrow('Check the form.')
    expect({ ...errors }).toEqual({ name: 'Required. Too short.' })
  })

  it('rethrows other errors without taking anything', () => {
    const { errors, capture } = useFieldErrors(reactive({ name: '' }))
    expect(() => capture(new Error('boom'))).toThrow('boom')
    expect(Object.keys(errors)).toEqual([])
  })

  it('gives the form item props of a field', () => {
    const { capture, item } = useFieldErrors(reactive({ name: '', email: '' }))
    expect(() => capture(failed({ name: ['Required.'] }))).toThrow('Check the form.')
    expect(item('name')).toEqual({
      showFeedback: false,
      validationStatus: 'error',
      'data-field-error': 'Required.',
    })
    expect(item('email')).toEqual({
      showFeedback: false,
      validationStatus: undefined,
      'data-field-error': undefined,
    })
  })

  it('drops the error of a field once its value changes', async () => {
    const form = reactive({ name: '', tags: ['a'] })
    const { errors, capture } = useFieldErrors(form)
    expect(() => capture(failed({ name: ['Required.'], tags: ['Invalid.'] }))).toThrow(
      'Check the form.',
    )
    form.name = 'Laptop'
    await nextTick()
    expect({ ...errors }).toEqual({ tags: 'Invalid.' })
    form.tags = ['a']
    await nextTick()
    // The same content is no change.
    expect({ ...errors }).toEqual({ tags: 'Invalid.' })
  })

  it('clears all errors', () => {
    const { errors, capture, clear } = useFieldErrors(reactive({ name: '' }))
    expect(() => capture(failed({ name: ['Required.'] }))).toThrow('Check the form.')
    clear()
    expect(Object.keys(errors)).toEqual([])
  })
})

describe('useScanner', () => {
  let now = 0
  beforeEach(() => {
    now = 1000
    vi.spyOn(performance, 'now').mockImplementation(() => now)
  })
  afterEach(() => vi.restoreAllMocks())

  function press(keys: string, gap = 10, target: EventTarget = window) {
    for (const key of keys.split(' ')) {
      now += gap
      target.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }))
    }
  }

  function scanner(options?: { minLength?: number; maxGap?: number }) {
    const onScan = vi.fn<(code: string) => void>()
    const { wrapper } = withSetup(() => useScanner(onScan, options))
    return { onScan, wrapper }
  }

  it('reports fast input that ends with Enter', () => {
    const { onScan, wrapper } = scanner()
    press('A 1 2 3 4 5 Enter')
    expect(onScan).toHaveBeenCalledWith('A12345')
    wrapper.unmount()
  })

  it('prevents the default of the closing Enter', () => {
    const { wrapper } = scanner()
    press('A 1 2 3 4')
    const enter = new KeyboardEvent('keydown', { key: 'Enter', cancelable: true })
    window.dispatchEvent(enter)
    expect(enter.defaultPrevented).toBe(true)
    wrapper.unmount()
  })

  it('ignores short codes', () => {
    const { onScan, wrapper } = scanner()
    press('1 2 3 Enter')
    expect(onScan).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('ignores slow typing by a person', () => {
    const { onScan, wrapper } = scanner()
    press('1 2 3 4 5 6 Enter', 200)
    expect(onScan).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('starts over after a pause', () => {
    const { onScan, wrapper } = scanner()
    press('X Y')
    now += 500
    press('1 2 3 4 5 Enter')
    expect(onScan).toHaveBeenCalledWith('12345')
    wrapper.unmount()
  })

  it('skips keys that are not characters', () => {
    const { onScan, wrapper } = scanner({ minLength: 3 })
    press('Shift A Shift B C Enter')
    expect(onScan).toHaveBeenCalledWith('ABC')
    wrapper.unmount()
  })

  it('leaves typing in input fields alone', () => {
    const { onScan, wrapper } = scanner()
    const input = document.createElement('input')
    document.body.append(input)
    press('1 2 3 4 5 Enter', 10, input)
    expect(onScan).not.toHaveBeenCalled()
    input.remove()
    wrapper.unmount()
  })

  it('stops listening when unmounted', () => {
    const { onScan, wrapper } = scanner()
    wrapper.unmount()
    press('1 2 3 4 5 Enter')
    expect(onScan).not.toHaveBeenCalled()
  })
})

describe('useAssigned', () => {
  async function assigned(storageKey: string, url = '/') {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { render: () => null } }],
    })
    await router.push(url)
    return withSetup(() => useAssigned(storageKey), [router]).result
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('shows all by default', async () => {
    const { assigned: value, param } = await assigned('requests')
    expect(value.value).toBe('all')
    expect(param(value.value)).toBeNull()
    expect(param('me')).toBe('me')
  })

  it('remembers the choice per list', async () => {
    const first = await assigned('requests')
    first.assigned.value = 'my_teams'
    await nextTick()
    expect((await assigned('requests')).assigned.value).toBe('my_teams')
    expect((await assigned('issues')).assigned.value).toBe('all')
  })

  it('lets the URL win over the remembered choice', async () => {
    localStorage.setItem('argus.requests.assigned', 'nobody')
    expect((await assigned('requests', '/?assigned=me')).assigned.value).toBe('me')
  })

  it('ignores unknown values in the URL and in storage', async () => {
    localStorage.setItem('argus.requests.assigned', 'everyone')
    expect((await assigned('requests', '/?assigned=bogus')).assigned.value).toBe('all')
  })

  it('works when storage is blocked', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const { assigned: value } = await assigned('requests')
    expect(value.value).toBe('all')
    value.value = 'me'
    await nextTick()
    expect(value.value).toBe('me')
    vi.restoreAllMocks()
  })
})

describe('useFormat', () => {
  const format = () => withSetup(() => useFormat(), [i18n]).result

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 20, 12, 0))
  })
  afterEach(() => vi.useRealTimers())

  it('shows a dash for empty values', () => {
    const f = format()
    for (const fn of [f.date, f.dateTime, f.dateWithWeekday, f.relativeDay, f.weekday, f.money]) {
      expect(fn(null)).toBe('—')
      expect(fn(undefined)).toBe('—')
    }
    expect(f.money('')).toBe('—')
    expect(f.enumLabel('assetStatus', null)).toBe('—')
  })

  it('formats dates and times in the user language', () => {
    const f = format()
    expect(f.date('2026-10-20')).toBe('10/20/2026')
    expect(f.dateTime('2026-10-20T13:33:00')).toBe('10/20/2026, 01:33 PM')
  })

  it('puts the weekday in front, with the time only when there is one', () => {
    const f = format()
    expect(f.dateWithWeekday('2026-10-20')).toBe('Tue 10/20/2026')
    expect(f.dateWithWeekday('2026-10-20T13:33:00')).toBe('Tue 10/20/2026 · 01:33 PM')
    expect(f.weekday('2026-10-20')).toBe('Tue Oct 20')
    expect(f.weekday(new Date(2026, 9, 20, 13, 33))).toBe('Tue Oct 20 · 01:33 PM')
  })

  it('drops the abbreviation dot of the German weekday', () => {
    i18n.global.locale.value = 'de'
    try {
      expect(format().weekday('2026-10-20')).toBe('Di 20. Okt.')
    } finally {
      i18n.global.locale.value = 'en'
    }
  })

  it('writes long dates for headings', () => {
    const f = format()
    expect(f.longDate('2026-10-20')).toBe('Tuesday, October 20')
    expect(f.longDate('2026-10-20T13:33:00', true)).toBe('Tuesday, October 20 · 01:33 PM')
    expect(f.longDate('2026-10-20', true)).toBe('Tuesday, October 20')
  })

  it('says how far away a day is', () => {
    const f = format()
    expect(f.relativeDay('2026-10-20')).toBe('Today')
    expect(f.relativeDay('2026-10-21')).toBe('Tomorrow')
    expect(f.relativeDay('2026-10-19')).toBe('Yesterday')
    expect(f.relativeDay('2026-10-23')).toBe('In 3 days')
    expect(f.relativeDay('2026-10-15')).toBe('5 days ago')
    expect(f.relativeDay('2026-10-21T20:00:00')).toBe('Tomorrow, 08:00 PM')
  })

  it('counts days across a DST change', () => {
    // Around the end of daylight saving time a day has 25 hours.
    vi.setSystemTime(new Date(2026, 9, 24, 23, 30))
    expect(format().relativeDay('2026-10-26')).toBe('In 2 days')
  })

  it('formats money in euros', () => {
    const f = format()
    expect(f.money('1234.5')).toBe('€1,234.50')
    expect(f.money(0)).toBe('€0.00')
  })

  it('translates enum values and keeps unknown ones', () => {
    const f = format()
    expect(f.enumLabel('assetStatus', 'in_stock')).toBe('In stock')
    expect(f.enumLabel('assetStatus', 'melted')).toBe('melted')
  })
})
