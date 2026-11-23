/**
 * Reading tables exported as CSV (MDM exports, spreadsheets saved as CSV).
 *
 * Handles quoted cells with separators, quotes ("") and line breaks inside, CRLF line
 * ends, a byte order mark, and the separator Excel uses in the respective locale.
 */

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

/** The non-empty records of a CSV text, header line included. */
export function parseCsv(input: string, delimiter = detectDelimiter(input)): string[][] {
  const text = input.replace(/^﻿/, '')
  const records: string[][] = []
  let record: string[] = []
  let cell = ''
  const endCell = () => {
    record.push(cell)
    cell = ''
  }
  const endRecord = () => {
    endCell()
    records.push(record)
    record = []
  }
  let i = 0
  while (i < text.length) {
    const char = text[i]!
    if (char === '"' && cell === '') {
      ;[cell, i] = readQuoted(text, i + 1)
      continue
    }
    if (char === delimiter) endCell()
    else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') i++
      endRecord()
    } else cell += char
    i++
  }
  if (cell !== '' || record.length) endRecord()
  return records.filter((r) => r.some((c) => c.trim() !== ''))
}

/** A quoted cell from `start` (after the opening quote): its text and the index after the closing quote. */
function readQuoted(text: string, start: number): [string, number] {
  let value = ''
  for (let i = start; i < text.length; i++) {
    const char = text[i]!
    if (char !== '"') value += char
    else if (text[i + 1] === '"') {
      value += '"'
      i++
    } else return [value, i + 1]
  }
  return [value, text.length]
}

/** UTF-8, or Windows-1252 for files that are not (older Excel "CSV" saves). */
export function decodeText(buffer: ArrayBuffer): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer)
  } catch {
    return new TextDecoder('windows-1252').decode(buffer)
  }
}
