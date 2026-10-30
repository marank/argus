import { globSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

import { describe, expect, it } from 'vitest'

import de from '@/i18n/locales/de'
import en from '@/i18n/locales/en'

// Every source file as text, to find the translation keys it uses literally. Read from
// disk rather than imported, so the files do not count as covered by this test.
// Vitest runs in the frontend directory (`root` in vitest.config.ts).
const root = join(process.cwd(), 'src')
const sources = Object.fromEntries(
  globSync('**/*.{ts,vue}', { cwd: root, exclude: ['__tests__/**'] }).map((file) => [
    file,
    readFileSync(join(root, file), 'utf8'),
  ]),
)

const KEY = /\$?\bt\(\s*'([\w.]+)'/g

function has(messages: unknown, key: string): boolean {
  let node = messages
  for (const part of key.split('.')) {
    if (typeof node !== 'object' || node === null || !(part in node)) return false
    node = (node as Record<string, unknown>)[part]
  }
  return typeof node === 'string'
}

describe('translation keys', () => {
  const used = Object.entries(sources).flatMap(([file, text]) =>
    [...text.matchAll(KEY)].map((match) => ({ file, key: match[1]! })),
  )

  it('finds the keys used in the code', () => {
    expect(used.length).toBeGreaterThan(500)
  })

  it.each([
    ['en', en],
    ['de', de],
  ])('every literal key exists in %s', (_, messages) => {
    const missing = used.filter(({ key }) => !has(messages, key)).map((u) => `${u.file}: ${u.key}`)
    expect(missing).toEqual([])
  })
})
