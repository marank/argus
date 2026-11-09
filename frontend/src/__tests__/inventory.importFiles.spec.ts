import { flushPromises } from '@vue/test-utils'
import * as webStreams from 'node:stream/web'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import { assetsApi } from '@/api/inventory'
import AssetImportModal from '@/components/inventory/AssetImportModal.vue'
import { guessHasHeader, readTableFile, toTable, UnsupportedFileError } from '@/utils/tableFile'
import { excelDate, readXlsx } from '@/utils/xlsx'

import { bodyText, mountPage, stubPickers } from './inventoryHelpers'

// Browsers have these; jsdom does not, Node does.
vi.stubGlobal('CompressionStream', webStreams.CompressionStream)
vi.stubGlobal('DecompressionStream', webStreams.DecompressionStream)

/** A ZIP archive of the given parts, deflated or stored. */
async function zip(parts: Record<string, string>, deflate = true): Promise<ArrayBuffer> {
  const encoder = new TextEncoder()
  const chunks: Uint8Array[] = []
  const directory: Uint8Array[] = []
  let offset = 0
  for (const [name, text] of Object.entries(parts)) {
    const raw = encoder.encode(text)
    const data = deflate
      ? new Uint8Array(
          await new Response(
            new Response(raw).body!.pipeThrough(new CompressionStream('deflate-raw')),
          ).arrayBuffer(),
        )
      : raw
    const nameBytes = encoder.encode(name)
    const local = new DataView(new ArrayBuffer(30))
    local.setUint32(0, 0x04034b50, true)
    local.setUint16(8, deflate ? 8 : 0, true)
    local.setUint32(18, data.length, true)
    local.setUint32(22, raw.length, true)
    local.setUint16(26, nameBytes.length, true)
    const central = new DataView(new ArrayBuffer(46))
    central.setUint32(0, 0x02014b50, true)
    central.setUint16(10, deflate ? 8 : 0, true)
    central.setUint32(20, data.length, true)
    central.setUint32(24, raw.length, true)
    central.setUint16(28, nameBytes.length, true)
    central.setUint32(42, offset, true)
    chunks.push(new Uint8Array(local.buffer), nameBytes, data)
    directory.push(new Uint8Array(central.buffer), nameBytes)
    offset += 30 + nameBytes.length + data.length
  }
  const size = directory.reduce((n, c) => n + c.length, 0)
  const end = new DataView(new ArrayBuffer(22))
  end.setUint32(0, 0x06054b50, true)
  end.setUint16(8, Object.keys(parts).length, true)
  end.setUint16(10, Object.keys(parts).length, true)
  end.setUint32(12, size, true)
  end.setUint32(16, offset, true)
  return new Blob([...chunks, ...directory, new Uint8Array(end.buffer)] as BlobPart[]).arrayBuffer()
}

const NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
const REL_NS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'

/** A workbook as Excel writes it: shared strings, a date style, two sheets. */
const WORKBOOK = {
  'xl/workbook.xml': `<?xml version="1.0"?><workbook ${NS} ${REL_NS}><sheets>
    <sheet name="Notes" sheetId="1" r:id="rId1"/><sheet name="Geräte" sheetId="2" r:id="rId2"/>
    </sheets></workbook>`,
  'xl/_rels/workbook.xml.rels': `<?xml version="1.0"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Target="worksheets/sheet1.xml"/>
    <Relationship Id="rId2" Target="/xl/worksheets/sheet2.xml"/></Relationships>`,
  'xl/sharedStrings.xml': `<sst ${NS}><si><t>Seriennummer</t></si><si><t>Kaufdatum</t></si>
    <si><r><t>31415</t></r><r><t>A926B</t></r><rPh><t>x</t></rPh></si><si><t>Preis</t></si></sst>`,
  'xl/styles.xml': `<styleSheet ${NS}><numFmts count="1"><numFmt numFmtId="164" formatCode="dd/mm/yyyy hh:mm"/></numFmts>
    <cellXfs count="4"><xf numFmtId="0"/><xf numFmtId="14"/><xf numFmtId="164"/><xf numFmtId="4"/></cellXfs></styleSheet>`,
  'xl/worksheets/sheet1.xml': `<worksheet ${NS}><sheetData/></worksheet>`,
  'xl/worksheets/sheet2.xml': `<worksheet ${NS}><sheetData>
    <row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="D1" t="s"><v>3</v></c></row>
    <row r="3"><c r="A3" t="s"><v>2</v></c><c r="B3" s="1"><v>46112</v></c><c r="C3" s="2"><v>46112.5</v></c>
      <c r="D3" s="3"><v>1234.5699999999999</v></c><c r="E3" t="b"><v>1</v></c><c r="F3" t="inlineStr"><is><t>H102</t></is></c>
      <c r="G3"><v>9.9001E+14</v></c><c r="H3" t="e"><v>#N/A</v></c><c r="I3" t="str"><v>HT60</v></c></row>
    </sheetData></worksheet>`,
}

describe('reading Excel files', () => {
  it('reads the sheets with strings, dates, numbers and gaps', async () => {
    const sheets = await readXlsx(await zip(WORKBOOK))
    expect(sheets.map((s) => s.name)).toEqual(['Notes', 'Geräte'])
    expect(sheets[0]!.rows).toEqual([])
    expect(sheets[1]!.rows).toEqual([
      ['Seriennummer', 'Kaufdatum', '', 'Preis'],
      [],
      [
        '31415A926B',
        '2026-03-31',
        '2026-03-31 12:00',
        '1234.57',
        'TRUE',
        'H102',
        '990010000000000',
        '',
        'HT60',
      ],
    ])
  })

  it('reads stored (uncompressed) parts too', async () => {
    const sheets = await readXlsx(await zip(WORKBOOK, false))
    expect(sheets[1]!.rows[0]![0]).toBe('Seriennummer')
  })

  it('refuses archives that are no workbook', async () => {
    await expect(readXlsx(await zip({ 'a.txt': 'x' }))).rejects.toThrow('not an Excel workbook')
    await expect(readXlsx(new ArrayBuffer(40))).rejects.toThrow('not a zip archive')
  })

  it('converts date serials in both date systems', () => {
    expect(excelDate(46112, 'date')).toBe('2026-03-31')
    expect(excelDate(0, 'date', true)).toBe('1904-01-01')
    expect(excelDate(46112.25, 'datetime')).toBe('2026-03-31 06:00')
  })

  it('tells CSV, xlsx and old xls files apart', async () => {
    const xlsx = new File([await zip(WORKBOOK)], 'Geräte.xlsx')
    expect((await readTableFile(xlsx))[1]!.name).toBe('Geräte')
    const csv = new File(['a;b\n1;2'], 'list.csv')
    expect(await readTableFile(csv)).toEqual([
      {
        name: 'list.csv',
        rows: [
          ['a', 'b'],
          ['1', '2'],
        ],
      },
    ])
    const xls = new File([new Uint8Array([0xd0, 0xcf, 0x11, 0xe0, 0, 0])], 'old.xls')
    await expect(readTableFile(xls)).rejects.toBeInstanceOf(UnsupportedFileError)
  })
})

describe('files without column names', () => {
  it('guesses from the first row whether it holds names', () => {
    expect(guessHasHeader([['Seriennummer', 'Wi-Fi-MAC']])).toBe(true)
    expect(guessHasHeader([['H102', '00:00:5e:00:53:01']])).toBe(false)
    expect(guessHasHeader([['H102', '192.0.2.87']])).toBe(false)
    expect(guessHasHeader([['31415A926B', '31.03.2026']])).toBe(false)
    expect(guessHasHeader([['H102', '990010902479923']])).toBe(false)
    expect(guessHasHeader([])).toBe(true)
  })

  it('numbers the columns and keeps every row', () => {
    const rows = [['H102', '0c:23'], [], ['H064', '00:10', 'extra']]
    expect(toTable(rows, false)).toEqual({
      headers: ['', '', ''],
      rows: [
        ['H102', '0c:23', ''],
        ['H064', '00:10', 'extra'],
      ],
    })
    expect(toTable(rows, true).headers).toEqual(['H102', '0c:23', ''])
  })
})

describe('AssetImportModal with Excel and headerless files', () => {
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

  async function openWith(file: File) {
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
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    input.dispatchEvent(new Event('change'))
    await vi.waitFor(() => expect(bodyText()).toMatch(/rows,|cannot be read|no rows/))
    await flushPromises()
  }

  const RESULT = { rows: [], created: 0, updated: 0, unchanged: 0, skipped: 0, failed: 0 }

  it('opens the first sheet with data and imports its rows', async () => {
    const preview = vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    await openWith(new File([await zip(WORKBOOK)], 'Geräte.xlsx'))
    expect(bodyText()).toContain('Geräte.xlsx: 1 rows, 9 columns')
    expect(document.querySelector('[data-test="sheet"]')).not.toBeNull()
    document.querySelector<HTMLElement>('[data-test="import-preview-button"]')!.click()
    await flushPromises()
    expect(preview.mock.calls[0]![0].rows).toEqual([
      { serial_number: '31415A926B', purchase_date: '2026-03-31', purchase_price: '1234.57' },
    ])
  })

  it('reads a file without column names and lets the user switch', async () => {
    const preview = vi.spyOn(assetsApi, 'importPreview').mockResolvedValue(RESULT)
    await openWith(new File(['H102;00:00:5e:00:53:01\nH064;00:00:5e:00:53:02\n'], 'macs.csv'))
    expect(bodyText()).toContain('macs.csv: 2 rows, 2 columns')
    // Numbered columns with their first value, none suggested.
    expect(bodyText()).toContain('First row holds the column names')
    document.querySelector<HTMLElement>('[data-test="import-preview-button"]')!.click()
    await flushPromises()
    expect(preview).not.toHaveBeenCalled()

    document.querySelector<HTMLElement>('[data-test="has-header"] .n-switch')!.click()
    await flushPromises()
    expect(bodyText()).toContain('macs.csv: 1 rows, 2 columns')
  })

  it('explains that old .xls files need saving as .xlsx', async () => {
    await openWith(new File([new Uint8Array([0xd0, 0xcf, 0x11, 0xe0])], 'old.xls'))
    expect(bodyText()).toContain('Old (.xls) or password-protected Excel files cannot be read.')
  })
})
