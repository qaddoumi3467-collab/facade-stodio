// Describes each catalog table: which fields its form has and which columns
// its list shows. Field keys match the API.

export type FieldType = 'text' | 'number' | 'checkbox' | 'select' | 'system'

export interface Field {
  key: string
  type: FieldType
  required?: boolean
  /** For select fields: the option values; labels come from `${optionPrefix}.${value}`. */
  options?: string[]
  optionPrefix?: string
  step?: string
}

export interface CatalogConfig {
  resource: 'systems' | 'profiles' | 'glass' | 'hardware'
  tab: string
  codeKey: 'code' | 'article_no'
  fields: Field[]
  /** Columns shown in the list besides code and name. */
  columns: string[]
  filterBySystem?: boolean
}

const names: Field[] = [
  { key: 'name_en', type: 'text', required: true },
  { key: 'name_ar', type: 'text', required: true },
]

export const ROLES = ['frame', 'sash', 'mullion', 'transom', 'glazing_bead', 'threshold', 'coupling', 'interlock', 'adaptor', 'cleat', 'flyscreen', 'other']
export const CATEGORIES = ['handle', 'hinge', 'lock', 'gasket', 'corner_cleat', 'roller', 'accessory', 'other']
export const UNITS = ['piece', 'set', 'metre']

export const CATALOGS: CatalogConfig[] = [
  {
    resource: 'systems',
    tab: 'tab.systems',
    codeKey: 'code',
    fields: [
      { key: 'code', type: 'text', required: true },
      ...names,
      { key: 'manufacturer', type: 'text' },
      { key: 'description', type: 'text' },
      { key: 'thermal_break', type: 'checkbox' },
      { key: 'sash_overlap_mm', type: 'number', required: true, step: '0.1' },
      { key: 'glass_bite_mm', type: 'number', required: true, step: '0.1' },
    ],
    columns: ['manufacturer', 'thermal_break'],
  },
  {
    resource: 'profiles',
    tab: 'tab.profiles',
    codeKey: 'article_no',
    filterBySystem: true,
    fields: [
      { key: 'system_id', type: 'system', required: true },
      { key: 'article_no', type: 'text', required: true },
      ...names,
      { key: 'role', type: 'select', options: ROLES, optionPrefix: 'role', required: true },
      { key: 'width_mm', type: 'number', required: true, step: '0.01' },
      { key: 'height_mm', type: 'number', required: true, step: '0.01' },
      { key: 'weight_kg_per_m', type: 'number', required: true, step: '0.001' },
      { key: 'bar_length_mm', type: 'number', required: true, step: '1' },
      { key: 'price_per_m', type: 'number', step: '0.01' },
    ],
    columns: ['system_id', 'role', 'width_mm', 'height_mm', 'weight_kg_per_m', 'price_per_m'],
  },
  {
    resource: 'glass',
    tab: 'tab.glass',
    codeKey: 'code',
    fields: [
      { key: 'code', type: 'text', required: true },
      ...names,
      { key: 'build_up', type: 'text' },
      { key: 'total_thickness_mm', type: 'number', required: true, step: '0.01' },
      { key: 'glass_thickness_mm', type: 'number', required: true, step: '0.01' },
      { key: 'u_value', type: 'number', step: '0.01' },
      { key: 'price_per_m2', type: 'number', step: '0.01' },
    ],
    columns: ['build_up', 'total_thickness_mm', 'glass_thickness_mm', 'u_value', 'price_per_m2'],
  },
  {
    resource: 'hardware',
    tab: 'tab.hardware',
    codeKey: 'article_no',
    filterBySystem: true,
    fields: [
      { key: 'system_id', type: 'system' },
      { key: 'article_no', type: 'text', required: true },
      ...names,
      { key: 'category', type: 'select', options: CATEGORIES, optionPrefix: 'category', required: true },
      { key: 'unit', type: 'select', options: UNITS, optionPrefix: 'unit', required: true },
      { key: 'price_per_unit', type: 'number', step: '0.01' },
    ],
    columns: ['system_id', 'category', 'unit', 'price_per_unit'],
  },
]

export const DEFAULTS: Record<string, unknown> = {
  bar_length_mm: 6000,
  role: 'frame',
  category: 'handle',
  unit: 'piece',
  thermal_break: false,
  sash_overlap_mm: 0,
  glass_bite_mm: 0,
}

/** Turn form strings into the JSON the API expects: numbers for number
 *  fields, null for empty optional fields. */
export function toPayload(fields: Field[], form: Record<string, unknown>) {
  const out: Record<string, unknown> = {}
  for (const f of fields) {
    const raw = form[f.key]
    if (f.type === 'checkbox') {
      out[f.key] = Boolean(raw)
    } else if (raw === '' || raw === undefined || raw === null) {
      out[f.key] = null
    } else if (f.type === 'number' || f.type === 'system') {
      out[f.key] = Number(raw)
    } else {
      out[f.key] = String(raw).trim()
    }
  }
  return out
}
