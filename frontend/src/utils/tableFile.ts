/**
 * Import files as tables: CSV or Excel (.xlsx), with or without a line of column names.
 */
import { decodeText, parseCsv } from '@/utils/csv'
import { readXlsx, type Sheet } from '@/utils/xlsx'

export type { Sheet }

export interface Table {
  /** Column names; empty strings for a file without them. */
  headers: string[]
  rows: string[][]
}

/** Neither CSV nor .xlsx, e.g. the binary .xls of Excel 97–2003. */
export class UnsupportedFileError extends Error {}

const ZIP_SIGNATURE = [0x50, 0x4b, 0x03, 0x04]
const OLE_SIGNATURE = [0xd0, 0xcf, 0x11, 0xe0]

const startsWith = (bytes: Uint8Array, signature: number[]) =>
  signature.every((b, i) => bytes[i] === b)

/** The sheets of the file: one for CSV, each worksheet of a workbook. */
export async function readTableFile(file: File): Promise<Sheet[]> {
  const buffer = await file.arrayBuffer()
  const head = new Uint8Array(buffer.slice(0, 4))
  if (startsWith(head, ZIP_SIGNATURE)) return readXlsx(buffer)
  if (startsWith(head, OLE_SIGNATURE)) throw new UnsupportedFileError(file.name)
  return [{ name: file.name, rows: parseCsv(decodeText(buffer)) }]
}

/** Rows as a table; with `hasHeader` the first row holds the column names. */
export function toTable(rows: string[][], hasHeader: boolean): Table {
  const data = rows.filter((r) => r.some((c) => c.trim() !== ''))
  const width = Math.max(0, ...data.map((r) => r.length))
  const [first = [], ...rest] = data
  const pad = (r: string[]) => Array.from({ length: width }, (_, i) => r[i] ?? '')
  if (hasHeader) return { headers: pad(first).map((h) => h.trim()), rows: rest.map(pad) }
  return { headers: Array<string>(width).fill(''), rows: data.map(pad) }
}

// Values that are data, not a column name: MAC and IP addresses, dates, long numbers.
const DATA_LIKE = [
  /^[0-9a-f]{2}([:-]?[0-9a-f]{2}){5}$/i,
  /^\d{1,3}(\.\d{1,3}){3}/,
  /^\d{4}-\d{2}-\d{2}/,
  /^\d{1,2}\.\d{1,2}\.\d{2,4}$/,
  /^[\d.,\s-]{5,}$/,
]

/** Whether the first row looks like column names: none of its cells looks like data. */
export function guessHasHeader(rows: string[][]): boolean {
  const first = rows.find((r) => r.some((c) => c.trim() !== ''))
  if (!first) return true
  return !first.some((cell) =>
    DATA_LIKE.some((pattern) => pattern.test(cell.trim().replace(/^'/, ''))),
  )
}
