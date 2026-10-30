import { describe, expect, it } from 'vitest'

import { allValues } from '@/utils/enums'

describe('allValues', () => {
  it('lists the values in the given order', () => {
    expect(allValues<'b' | 'a'>({ b: true, a: true })).toEqual(['b', 'a'])
  })

  it('fails the type check when a value is missing or unknown', () => {
    // @ts-expect-error 'b' is missing
    expect(allValues<'a' | 'b'>({ a: true })).toEqual(['a'])
    // @ts-expect-error 'c' is not a value
    expect(allValues<'a'>({ a: true, c: true })).toEqual(['a', 'c'])
  })
})
