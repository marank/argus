/**
 * Reading the sheets of an Excel workbook (.xlsx) as rows of text, without a library:
 * the file is a ZIP archive of XML parts, which the browser can inflate
 * (`DecompressionStream`) and parse (`DOMParser`).
 *
 * Cells come as Excel shows them where it matters for an import: shared and inline
 * strings as text, dates as ISO dates (`2026-03-31`, with the time if the format shows
 * one), numbers in their shortest form, booleans as TRUE/FALSE.
 */

export interface Sheet {
  name: string
  rows: string[][]
}

/** The files of a ZIP archive by name (stored or deflated entries). */
async function unzip(buffer: ArrayBuffer): Promise<Map<string, Uint8Array>> {
  const bytes = new Uint8Array(buffer)
  const view = new DataView(buffer)
  // The end of central directory record is in the last 64 KiB (comment included).
  let end = -1
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
    if (view.getUint32(i, true) === 0x06054b50) {
      end = i
      break
    }
  }
  if (end < 0) throw new Error('not a zip archive')
  const count = view.getUint16(end + 10, true)
  let offset = view.getUint32(end + 16, true)
  const files = new Map<string, Uint8Array>()
  const decoder = new TextDecoder()
  for (let n = 0; n < count; n++) {
    if (view.getUint32(offset, true) !== 0x02014b50) throw new Error('broken zip directory')
    const method = view.getUint16(offset + 10, true)
    const size = view.getUint32(offset + 20, true)
    const nameLength = view.getUint16(offset + 28, true)
    const extraLength = view.getUint16(offset + 30, true)
    const commentLength = view.getUint16(offset + 32, true)
    const local = view.getUint32(offset + 42, true)
    const name = decoder.decode(bytes.subarray(offset + 46, offset + 46 + nameLength))
    offset += 46 + nameLength + extraLength + commentLength

    const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true)
    const data = bytes.subarray(start, start + size)
    if (method === 0) files.set(name, data)
    else if (method === 8) files.set(name, await inflate(data))
    // Other methods do not occur in workbooks; such parts are left out.
  }
  return files
}

async function inflate(data: Uint8Array): Promise<Uint8Array> {
  const stream = new Response(data as BodyInit).body!.pipeThrough(
    new DecompressionStream('deflate-raw'),
  )
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

function xml(files: Map<string, Uint8Array>, path: string): Document | null {
  const data = files.get(path)
  if (!data) return null
  return new DOMParser().parseFromString(new TextDecoder().decode(data), 'application/xml')
}

/** Elements by local name, whatever prefix the writer used (`c`, `x:c`). */
const all = (
  node: ParentNode & { getElementsByTagNameNS: Document['getElementsByTagNameNS'] },
  name: string,
) => [...node.getElementsByTagNameNS('*', name)]

/** The text of a string item: plain `<t>`, or the runs of rich text (phonetic hints left out). */
function stringText(item: Element): string {
  return all(item, 't')
    .filter((t) => t.parentElement?.localName !== 'rPh')
    .map((t) => t.textContent)
    .join('')
}

// Built-in number formats that show a date (14–22, 45–47 and the East Asian ones).
const DATE_FORMAT_IDS = new Set([
  14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 30, 36, 45, 46, 47, 50, 57,
])
const TIME_FORMAT_IDS = new Set([18, 19, 20, 21, 22, 45, 46, 47])

type CellFormat = 'date' | 'datetime' | null

function cellFormats(styles: Document | null): CellFormat[] {
  if (!styles) return []
  const custom = new Map<number, string>()
  for (const format of all(styles, 'numFmt'))
    custom.set(Number(format.getAttribute('numFmtId')), format.getAttribute('formatCode') ?? '')
  const cellXfs = all(styles, 'cellXfs')[0]
  if (!cellXfs) return []
  return all(cellXfs, 'xf').map((xf) => {
    const id = Number(xf.getAttribute('numFmtId') ?? 0)
    const code = custom.get(id)
    if (code !== undefined) {
      // Quoted text, escapes and colors aside, a date format has d, m or y.
      const bare = code.replace(/"[^"]*"|\\.|\[[^\]]*\]/g, '')
      if (!/[dy]|m(?!s)/i.test(bare) || /^[#0.,%\s]*$/.test(bare)) return null
      return /h|s/i.test(bare) ? 'datetime' : 'date'
    }
    if (TIME_FORMAT_IDS.has(id)) return 'datetime'
    return DATE_FORMAT_IDS.has(id) ? 'date' : null
  })
}

/** An Excel date serial (days since 1899-12-30, or 1904-01-01) as ISO text. */
export function excelDate(serial: number, format: 'date' | 'datetime', date1904 = false): string {
  const epoch = date1904 ? Date.UTC(1904, 0, 1) : Date.UTC(1899, 11, 30)
  const iso = new Date(epoch + Math.round(serial * 86400) * 1000).toISOString()
  return format === 'date' ? iso.slice(0, 10) : `${iso.slice(0, 10)} ${iso.slice(11, 16)}`
}

/** Column index of a cell reference: A1 → 0, AB7 → 27. */
function columnIndex(reference: string): number {
  let index = 0
  for (const char of reference.replace(/\d+$/, '')) index = index * 26 + char.charCodeAt(0) - 64
  return index - 1
}

/** The text of one cell, by its SpreadsheetML type. */
function cellText(
  cell: Element,
  strings: string[],
  formats: CellFormat[],
  date1904: boolean,
): string {
  const value = all(cell, 'v')[0]?.textContent ?? ''
  const type = cell.getAttribute('t')
  if (type === 's') return strings[Number(value)] ?? ''
  if (type === 'inlineStr') return stringText(all(cell, 'is')[0] ?? cell)
  if (type === 'b') return value === '1' ? 'TRUE' : 'FALSE'
  if (type === 'e') return ''
  if (type === 'str' || value === '') return value
  const format = formats[Number(cell.getAttribute('s') ?? 0)]
  // String() gives the shortest form: 1234.5699999999999 → 1234.57, 9.9E+14 → 990000000000000.
  const number = Number(value)
  return format ? excelDate(number, format, date1904) : String(number)
}

function readSheet(
  document: Document,
  strings: string[],
  formats: CellFormat[],
  date1904: boolean,
): string[][] {
  const rows: string[][] = []
  for (const row of all(document, 'row')) {
    const index = Number(row.getAttribute('r') ?? rows.length + 1) - 1
    const cells: string[] = []
    for (const cell of all(row, 'c')) {
      const reference = cell.getAttribute('r')
      const column = reference ? columnIndex(reference) : cells.length
      cells[column] = cellText(cell, strings, formats, date1904)
    }
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- skipped cells leave holes, undefined at runtime
    rows[index] = Array.from(cells, (c) => c ?? '')
  }
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- skipped rows leave holes, undefined at runtime
  return Array.from(rows, (r) => r ?? [])
}

export async function readXlsx(buffer: ArrayBuffer): Promise<Sheet[]> {
  const files = await unzip(buffer)
  const workbook = xml(files, 'xl/workbook.xml')
  if (!workbook) throw new Error('not an Excel workbook')
  const date1904 = ['1', 'true'].includes(
    all(workbook, 'workbookPr')[0]?.getAttribute('date1904') ?? '',
  )

  const targets = new Map<string, string>()
  for (const rel of all(xml(files, 'xl/_rels/workbook.xml.rels') ?? workbook, 'Relationship')) {
    const target = rel.getAttribute('Target') ?? ''
    targets.set(
      rel.getAttribute('Id') ?? '',
      target.startsWith('/') ? target.slice(1) : `xl/${target}`,
    )
  }
  const shared = xml(files, 'xl/sharedStrings.xml')
  const strings = shared ? all(shared, 'si').map(stringText) : []
  const formats = cellFormats(xml(files, 'xl/styles.xml'))

  const sheets: Sheet[] = []
  for (const sheet of all(workbook, 'sheet')) {
    const id = sheet.getAttributeNS(
      'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'id',
    )
    const document = xml(files, targets.get(id ?? '') ?? '')
    if (!document) continue
    sheets.push({
      name: sheet.getAttribute('name') ?? '',
      rows: readSheet(document, strings, formats, date1904),
    })
  }
  return sheets
}
