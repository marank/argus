/**
 * Reading tables exported as CSV (MDM exports, spreadsheets saved as CSV).
 *
 * Handles quoted cells with separators, quotes ("") and line breaks inside, CRLF line
 * ends, a byte order mark, and the separator Excel uses in the respective locale.
 */

export interface Table {
  headers: string[]
  rows: string[][]
  delimiter: string
}

const DELIMITERS = [',', ';', '\t', '|']

/** The separator that appears most often outside quotes in the first line. */
export function detectDelimiter(text: string): string {
  const counts = new Map(DELIMITERS.map((d) => [d, 0]))
  let quoted = false
  for (const char of text) {
    if (char === '"') quoted = !quoted
    else if (!quoted && (char === '\n' || char === '\r')) break
    else if (!quoted && counts.has(char)) counts.set(char, counts.get(char)! + 1)
  }
  let best = ','
  for (const [delimiter, count] of counts) if (count > counts.get(best)!) best = delimiter
  return best
}

export function parseCsv(input: string, delimiter = detectDelimiter(input)): Table {
  const text = input.replace(/^﻿/, '')
  const records: string[][] = []
  let record: string[] = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const char = text[i]!
    if (quoted) {
      if (char !== '"') cell += char
      else if (text[i + 1] === '"') {
        cell += '"'
        i++
      } else quoted = false
    } else if (char === '"' && cell === '') quoted = true
    else if (char === delimiter) {
      record.push(cell)
      cell = ''
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') i++
      record.push(cell)
      records.push(record)
      record = []
      cell = ''
    } else cell += char
  }
  if (cell !== '' || record.length) {
    record.push(cell)
    records.push(record)
  }
  const nonEmpty = records.filter((r) => r.some((c) => c.trim() !== ''))
  const [headers = [], ...rows] = nonEmpty
  return { headers: headers.map((h) => h.trim()), rows, delimiter }
}

/** UTF-8, or Windows-1252 for files that are not (older Excel "CSV" saves). */
export function decodeText(buffer: ArrayBuffer): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer)
  } catch {
    return new TextDecoder('windows-1252').decode(buffer)
  }
}

export async function readCsvFile(file: File): Promise<Table> {
  return parseCsv(decodeText(await file.arrayBuffer()))
}
