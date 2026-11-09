import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import { assetsApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import AssetImportModal from '@/components/inventory/AssetImportModal.vue'
import {
  emptyMapping,
  loadSettings,
  mapRows,
  sampleValue,
  saveSettings,
  suggestMapping,
} from '@/utils/assetImport'
import { decodeText, detectDelimiter, parseCsv } from '@/utils/csv'
import { toTable } from '@/utils/tableFile'

import { button, click } from './dom'
import { bodyText, mountPage, stubPickers } from './inventoryHelpers'

// The head of an MDM export (Fleetwise MDM), shortened.
const EXPORT = [
  'Nutzername,Gerätename,Gerätemodell,Wi-Fi-MAC,IP-Adresse,Seriennummer,Modellnr.,IMEI,Ort',
  'Administrator,H102,HT60,00:00:5e:00:53:01,"192.0.2.87,fe80::1",31415A926B,HT60,\'--,\'--',
  'Administrator,H064,HT60,00:00:5e:00:53:02,"192.0.2.26,fe80::2",27182B8281,HT60,\'--,\'--',
].join('\r\n')

const csvTable = (text: string) => toTable(parseCsv(text), true)

describe('reading CSV', () => {
  it('handles quotes, separators and line breaks inside cells', () => {
    expect(parseCsv('﻿a;b;c\n1;"x;""y""\nz";3\n\n')).toEqual([
      ['a', 'b', 'c'],
      ['1', 'x;"y"\nz', '3'],
    ])
  })

  it('detects the separator outside quotes', () => {
    expect(detectDelimiter('"a,b,c";d;e\n')).toBe(';')
    expect(detectDelimiter('a\tb\tc')).toBe('\t')
    expect(detectDelimiter('a,b')).toBe(',')
  })

  it('falls back to Windows-1252 for files that are not UTF-8', () => {
    const latin = new Uint8Array([0x47, 0x65, 0x72, 0xe4, 0x74]) // "Gerät"
    expect(decodeText(latin.buffer)).toBe('Gerät')
    expect(decodeText(new TextEncoder().encode('Gerät').buffer)).toBe('Gerät')
  })
})

describe('mapping columns', () => {
  const table = csvTable(EXPORT)

  it('suggests fields from the column names, each column once', () => {
    const mapping = suggestMapping(table.headers)
    expect(mapping.hostname).toBe(1)
    expect(mapping.model).toBe(2)
    expect(mapping.mac_address).toBe(3)
    expect(mapping.serial_number).toBe(5)
    expect(mapping.imei).toBe(7)
    expect(mapping.assigned_to).toBeNull()
    expect(mapping.location).toBeNull()
  })

  it('shows the first real value and maps rows to fields', () => {
    const mapping = suggestMapping(table.headers)
    expect(sampleValue(table.rows, mapping.serial_number)).toBe('31415A926B')
    expect(sampleValue(table.rows, mapping.imei)).toBe('')
    expect(mapRows(table.rows, mapping)[0]).toEqual({
      serial_number: '31415A926B',
      imei: "'--",
      mac_address: '00:00:5e:00:53:01',
      hostname: 'H102',
      model: 'HT60',
    })
  })
})

const RESULT: Schemas['AssetImportResultOut'] = {
  rows: [
    {
      row: 1,
      action: 'create',
      asset_id: null,
      inventory_number: 'MDE-0042',
      model: 'Handtec HT60',
      changes: [{ field: 'hostname', old: '', new: 'H102' }],
      errors: [],
    },
    {
      row: 2,
      action: 'error',
      asset_id: null,
      inventory_number: '',
      model: '',
      changes: [],
      errors: ['Model “CT61” not found.'],
    },
  ],
  created: 1,
  updated: 0,
  unchanged: 0,
  skipped: 0,
  failed: 1,
}

describe('AssetImportModal', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
    localStorage.clear()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function openWithFile() {
    const state = reactive({
      show: false,
      'onUpdate:show': (value: boolean) => (state.show = value),
      onImported: vi.fn<() => void>(),
    })
    const { wrapper } = await mountPage(AssetImportModal, state)
    unmount = () => wrapper.unmount()
    state.show = true
    await flushPromises()
    const input = document.querySelector<HTMLInputElement>('[data-test="import-file"]')!
    const file = new File([EXPORT], 'DeviceList.csv', { type: 'text/csv' })
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    input.dispatchEvent(new Event('change'))
    await vi.waitFor(() => expect(bodyText()).toContain('DeviceList.csv: 2 rows, 9 columns'))
    return state
  }

  it('reads the file, previews and imports with the mapped columns', async () => {
    const preview = vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    const run = vi.spyOn(assetsApi, 'import').mockResolvedValue({ ...RESULT })
    const state = await openWithFile()
    expect(bodyText()).toContain('31415A926B')

    await click('Show preview')
    const sent = preview.mock.calls[0]![0]
    expect(sent.match_by).toBe('serial_number')
    expect(sent.existing).toBe('update')
    expect(sent.ignore_case).toBe(false)
    expect(sent.rows[1]).toMatchObject({ serial_number: '27182B8281', hostname: 'H064' })
    // Rows with errors are shown first.
    expect(bodyText()).toContain('Model “CT61” not found.')
    expect(bodyText()).not.toContain('MDE-0042')
    const all = [...document.querySelectorAll('.n-radio-button')].find(
      (b) => b.textContent?.trim() === 'All',
    )
    all!.querySelector('input')!.click()
    await flushPromises()
    expect(bodyText()).toContain('MDE-0042')
    expect(run).not.toHaveBeenCalled()

    await click('Import 1 devices')
    expect(run).toHaveBeenCalledWith(sent)
    expect(state.onImported).toHaveBeenCalled()
    expect(bodyText()).toContain('Import finished.')
    expect(button('Close')).toBeTruthy()
  })

  it('remembers the settings for files with the same columns', async () => {
    vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    await openWithFile()
    await click('Show preview')
    const stored = loadSettings(csvTable(EXPORT).headers)
    expect(stored?.mapping.serial_number).toBe(5)
    expect(stored?.matchBy).toBe('serial_number')
  })
})

describe('AssetImportModal edge cases', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
    localStorage.clear()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function open() {
    const state = reactive({
      show: false,
      'onUpdate:show': (value: boolean) => (state.show = value),
      onImported: vi.fn<() => void>(),
    })
    const { wrapper } = await mountPage(AssetImportModal, state)
    unmount = () => wrapper.unmount()
    state.show = true
    await flushPromises()
    return state
  }

  async function choose(content: string, name = 'DeviceList.csv') {
    const input = document.querySelector<HTMLInputElement>('[data-test="import-file"]')!
    Object.defineProperty(input, 'files', {
      value: [new File([content], name, { type: 'text/csv' })],
      configurable: true,
    })
    input.dispatchEvent(new Event('change'))
    await vi.waitFor(() => expect(document.body.textContent).toMatch(/rows|no rows|could not/))
    await flushPromises()
  }

  it('says when the file holds no rows and stays on the first step', async () => {
    await open()
    await choose('Seriennummer,Gerätename\n')
    expect(bodyText()).toContain('The file holds no rows below the column names.')
    expect(button('Choose CSV or Excel file')).toBeTruthy()
  })

  it('goes back to the mapping and to another file, and shows changed values', async () => {
    const update: Schemas['AssetImportResultOut'] = {
      ...RESULT,
      rows: [
        {
          row: 1,
          action: 'update',
          asset_id: 'a1',
          inventory_number: 'MDE-0001',
          model: 'Handtec HT60',
          changes: [{ field: 'hostname', old: 'OLD-HOST', new: 'H102' }],
          errors: [],
        },
      ],
      created: 0,
      updated: 1,
      failed: 0,
    }
    vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(update)
    await open()
    await choose(EXPORT)
    await click('Show preview')
    expect(bodyText()).toContain('OLD-HOST')
    expect(bodyText()).toContain('H102')
    expect(bodyText()).toContain('Update: 1')

    await click('Back')
    expect(bodyText()).toContain('DeviceList.csv: 2 rows, 9 columns')
    await click('Other file')
    expect(button('Choose CSV or Excel file')).toBeTruthy()
  })

  it('takes over the settings of the last file with the same columns', async () => {
    const preview = vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    const headers = csvTable(EXPORT).headers
    saveSettings(headers, {
      mapping: { ...emptyMapping(), serial_number: 5, location: 99 },
      defaults: { model: 'm1', location: null, status: 'in_stock', condition: null },
      matchBy: null,
      existing: 'skip',
      ignoreCase: true,
    })
    await open()
    await choose(EXPORT)
    await click('Show preview')
    const sent = preview.mock.calls[0]![0]
    expect(sent.match_by).toBeNull()
    expect(sent.ignore_case).toBe(true)
    expect(sent.defaults).toMatchObject({ model: 'm1', status: 'in_stock' })
    // Only the stored column the file has; unknown columns are dropped.
    expect(sent.rows[0]).toEqual({ serial_number: '31415A926B' })
  })

  it('sends the switch to ignore case and remembers it', async () => {
    const preview = vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    await open()
    await choose(EXPORT)
    expect(bodyText()).toContain('Ignore upper and lower case')
    document.querySelector<HTMLElement>('[data-test="ignore-case"] .n-switch')!.click()
    await flushPromises()
    await click('Show preview')
    expect(preview.mock.calls[0]![0].ignore_case).toBe(true)
    expect(loadSettings(csvTable(EXPORT).headers)?.ignoreCase).toBe(true)
  })
})
