import type { LayoutNode, Opening, Path } from './layout'

export type Row = { id: number } & Record<string, unknown>

/** An API error. ``code`` is set when the server gives one (the element
 *  designer does), so the screen can show it in the user's language. */
export class ApiError extends Error {
  code?: string
  constructor(message: string, code?: string) {
    super(message)
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    if (detail && typeof detail === 'object' && 'code' in detail) {
      throw new ApiError(String(detail.message), String(detail.code))
    }
    const message = Array.isArray(detail)
      ? detail.map((d: { loc?: string[]; msg: string }) => `${d.loc?.at(-1) ?? ''}: ${d.msg}`).join('; ')
      : (detail ?? res.statusText)
    throw new ApiError(message)
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

export const api = {
  list: (resource: string, params: Record<string, string> = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== ''))
    const qs = query.toString()
    return request<Row[]>(`/${resource}${qs ? `?${qs}` : ''}`)
  },
  create: (resource: string, data: Record<string, unknown>) =>
    request<Row>(`/${resource}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (resource: string, id: number, data: Record<string, unknown>) =>
    request<Row>(`/${resource}/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  remove: (resource: string, id: number) =>
    request<void>(`/${resource}/${id}`, { method: 'DELETE' }),
  profilePiece: (id: number, lengthMm: number) =>
    request<{ weight_kg: number; price: number | null }>(
      `/profiles/${id}/piece?length_mm=${lengthMm}`,
    ),
  glassPane: (id: number, widthMm: number, heightMm: number) =>
    request<{ area_m2: number; weight_kg: number; price: number | null }>(
      `/glass/${id}/pane?width_mm=${widthMm}&height_mm=${heightMm}`,
    ),

  elements: () => request<SavedElement[]>('/elements'),
  calculateElement: (element: ElementData, signal?: AbortSignal) =>
    request<Calculation>('/elements/calculate', {
      method: 'POST',
      body: JSON.stringify(element),
      signal,
    }),
  saveElement: (element: ElementData, id?: number) =>
    request<SavedElement>(id ? `/elements/${id}` : '/elements', {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(element),
    }),
  deleteElement: (id: number) => request<void>(`/elements/${id}`, { method: 'DELETE' }),
}

// Element designer

export interface ElementData {
  position: string
  name: string
  quantity: number
  system_id: number
  width_mm: number
  height_mm: number
  frame_profile_id: number
  mullion_profile_id: number | null
  transom_profile_id: number | null
  sash_profile_id: number | null
  bead_profile_id: number | null
  glass_id: number
  layout: LayoutNode
}

export interface SavedElement extends ElementData {
  id: number
  updated_at: string
}

export interface Rect {
  x: number
  y: number
  width: number
  height: number
}

export interface Calculation {
  geometry: {
    width_mm: number
    height_mm: number
    frame_face_mm: number
    sash_face_mm: number | null
    dividers: { path: Path; direction: 'vertical' | 'horizontal'; rect: Rect; length_mm: number }[]
    fields: {
      path: Path
      opening: Opening
      glass_id: number
      clear: Rect
      sash: Rect | null
      glass_width_mm: number
      glass_height_mm: number
    }[]
  }
  profiles: {
    profile_id: number
    article_no: string
    name_en: string
    name_ar: string
    role: string
    length_mm: number
    angle_start: number
    angle_end: number
    quantity: number
    weight_kg: number
    price: number | null
  }[]
  glass: {
    glass_id: number
    code: string
    name_en: string
    name_ar: string
    width_mm: number
    height_mm: number
    quantity: number
    area_m2: number
    weight_kg: number
    price: number | null
  }[]
  totals: {
    profile_weight_kg: number
    glass_weight_kg: number
    glass_area_m2: number
    weight_kg: number
    price: number
    price_complete: boolean
  }
}
