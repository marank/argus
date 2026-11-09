/**
 * Mapping the columns of an import file to device fields: suggestions from the column
 * names, and the mapping remembered per file layout, so the next export of the same
 * system is mapped already.
 */
import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export type ImportField = Schemas['ImportField']
export type ImportMatch = Schemas['ImportMatch']
/** Column index per device field; `null`: not imported. */
export type ColumnMapping = Record<ImportField, number | null>

export const IMPORT_FIELDS = allValues<ImportField>({
  inventory_number: true,
  serial_number: true,
  identifier: true,
  imei: true,
  mac_address: true,
  name: true,
  model: true,
  status: true,
  condition: true,
  location: true,
  assigned_to: true,
  supplier: true,
  purchase_date: true,
  purchase_price: true,
  warranty_until: true,
  notes: true,
})

export const IMPORT_MATCHES = allValues<ImportMatch>({
  serial_number: true,
  inventory_number: true,
  imei: true,
  mac_address: true,
  name: true,
})

/** i18n key of each field's label. */
export const FIELD_LABELS: Record<ImportField, string> = {
  inventory_number: 'inventory.fields.inventoryNumber',
  serial_number: 'inventory.fields.serialNumber',
  identifier: 'inventory.fields.identifier',
  imei: 'inventory.fields.imei',
  mac_address: 'inventory.fields.macAddress',
  name: 'inventory.fields.name',
  model: 'inventory.fields.model',
  status: 'common.status',
  condition: 'inventory.fields.condition',
  location: 'inventory.fields.location',
  assigned_to: 'inventory.fields.assignedTo',
  supplier: 'inventory.fields.supplier',
  purchase_date: 'inventory.fields.purchaseDate',
  purchase_price: 'inventory.fields.purchasePrice',
  warranty_until: 'inventory.fields.warrantyUntil',
  notes: 'common.notes',
}

/** Column names (German and English, as exports name them) per field, best first. */
const SYNONYMS: Record<ImportField, string[]> = {
  inventory_number: ['inventarnummer', 'inventarnr', 'inventorynumber', 'inventoryno', 'assettag'],
  serial_number: ['seriennummer', 'seriennr', 'serialnumber', 'serialno', 'serial', 'sn'],
  identifier: ['identifier', 'kennung', 'cn', 'mtm', 'configurationnumber'],
  imei: ['imei', 'imei1'],
  mac_address: ['wifimac', 'wlanmac', 'macadresse', 'macaddress', 'mac'],
  name: ['hostname', 'gerätename', 'devicename', 'computername'],
  model: ['gerätemodell', 'devicemodel', 'modell', 'model', 'modellnr', 'produktbezeichnung'],
  status: ['status', 'gerätestatus', 'devicestatus'],
  condition: ['zustand', 'condition'],
  location: ['standort', 'location'],
  assigned_to: ['zugewiesenan', 'assignedto', 'benutzer', 'mitarbeiter'],
  supplier: ['lieferant', 'supplier', 'vendor'],
  purchase_date: ['kaufdatum', 'purchasedate', 'einkaufsdatum'],
  purchase_price: ['einkaufspreis', 'kaufpreis', 'purchaseprice', 'preis', 'price'],
  warranty_until: ['garantieablaufdatum', 'garantiebis', 'warrantyuntil', 'warrantyexpiration'],
  notes: ['bemerkungen', 'notizen', 'notes', 'remarks'],
}

const normalize = (name: string) => name.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '')

export function emptyMapping(): ColumnMapping {
  return Object.fromEntries(IMPORT_FIELDS.map((f) => [f, null])) as ColumnMapping
}

/** Fields whose column name is a known name for them; each column at most once. */
export function suggestMapping(headers: string[]): ColumnMapping {
  const mapping = emptyMapping()
  const names = headers.map(normalize)
  const used = new Set<number>()
  for (const field of IMPORT_FIELDS) {
    for (const synonym of SYNONYMS[field]) {
      const index = names.findIndex((name, i) => name === synonym && !used.has(i))
      if (index >= 0) {
        mapping[field] = index
        used.add(index)
        break
      }
    }
  }
  return mapping
}

/** The first cell of a column that holds a value (exports write `'--` for none). */
export function sampleValue(rows: string[][], column: number | null): string {
  if (column === null) return ''
  for (const row of rows) {
    const value = (row[column] ?? '').trim().replace(/^'/, '')
    if (value && !/^[-–—]+$/.test(value)) return value
  }
  return ''
}

/** Each row as `{field: cell}` for the mapped fields. */
export function mapRows(rows: string[][], mapping: ColumnMapping): Record<string, string>[] {
  const mapped = IMPORT_FIELDS.filter((f) => mapping[f] !== null)
  return rows.map((row) => Object.fromEntries(mapped.map((f) => [f, row[mapping[f]!] ?? ''])))
}

/** Settings remembered for files with the same columns. */
export interface ImportSettings {
  mapping: ColumnMapping
  defaults: Schemas['AssetImportDefaultsIn']
  matchBy: ImportMatch | null
  existing: Schemas['ExistingDevices']
  /** Missing in settings stored before the switch existed. */
  ignoreCase?: boolean
}

function layoutKey(headers: string[]): string {
  let hash = 5381
  for (const char of headers.join('\u0001')) hash = ((hash * 33) ^ char.charCodeAt(0)) >>> 0
  return `argus.assetImport.${headers.length}.${hash.toString(36)}`
}

export function loadSettings(headers: string[]): ImportSettings | null {
  try {
    const stored = localStorage.getItem(layoutKey(headers))
    if (!stored) return null
    const settings = JSON.parse(stored) as ImportSettings
    // Keep only fields this version knows, with columns the file has.
    const mapping = emptyMapping()
    for (const field of IMPORT_FIELDS) {
      const column = settings.mapping?.[field]
      if (typeof column === 'number' && column < headers.length) mapping[field] = column
    }
    return { ...settings, mapping }
  } catch {
    return null
  }
}

export function saveSettings(headers: string[], settings: ImportSettings) {
  try {
    localStorage.setItem(layoutKey(headers), JSON.stringify(settings))
  } catch {
    // Storage full or blocked: the next import starts from the suggestions.
  }
}
