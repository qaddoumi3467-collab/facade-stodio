export type Row = { id: number } & Record<string, unknown>

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((d: { loc?: string[]; msg: string }) => `${d.loc?.at(-1) ?? ''}: ${d.msg}`).join('; ')
      : (detail ?? res.statusText)
    throw new Error(message)
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
}
