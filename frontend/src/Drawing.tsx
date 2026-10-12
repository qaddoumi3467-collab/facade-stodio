import type { Calculation, Rect } from './api'
import { pathKey, type Opening, type Path } from './layout'

type Geometry = Calculation['geometry']

const inset = (r: Rect, by: number): Rect => ({
  x: r.x + by,
  y: r.y + by,
  width: r.width - 2 * by,
  height: r.height - 2 * by,
})

const fmt = (n: number) => String(Math.round(n * 10) / 10)

/** The element as seen from inside, with sizes in mm. Click a field to
 *  select it. */
export function Drawing(props: {
  geometry: Geometry
  selected: Path | null
  onSelect: (path: Path) => void
  stale?: boolean
}) {
  const g = props.geometry
  const W = g.width_mm
  const H = g.height_mm
  const big = Math.max(W, H)
  const pad = big * 0.16
  const font = big / 32
  const selectedKey = props.selected ? pathKey(props.selected) : null

  // Dimension chains: every divider centre line, plus the outer edges.
  const xs = uniqueSorted([0, W, ...g.dividers.filter((d) => d.direction === 'vertical').map((d) => d.rect.x + d.rect.width / 2)])
  const ys = uniqueSorted([0, H, ...g.dividers.filter((d) => d.direction === 'horizontal').map((d) => d.rect.y + d.rect.height / 2)])

  return (
    <svg
      className={props.stale ? 'drawing stale' : 'drawing'}
      viewBox={`${-pad * 0.4} ${-pad * 0.4} ${W + pad * 1.4} ${H + pad * 1.4}`}
      style={{ direction: 'ltr', fontSize: font }}
      role="img"
    >
      <rect className="frame" x={0} y={0} width={W} height={H} />
      {g.dividers.map((d, i) => (
        <rect key={i} className="divider" {...d.rect} />
      ))}

      {g.fields.map((f) => {
        const key = pathKey(f.path)
        const glassArea = f.sash && g.sash_face_mm ? inset(f.sash, g.sash_face_mm) : f.clear
        return (
          <g key={key} className={key === selectedKey ? 'field selected' : 'field'} onClick={() => props.onSelect(f.path)}>
            <rect className="opening-bg" {...f.clear} />
            {f.sash && <rect className="sash" {...f.sash} />}
            <rect className="glass" {...glassArea} />
            <OpeningSymbol opening={f.opening} r={glassArea} />
            <rect className="hit" {...(f.sash ?? f.clear)} />
          </g>
        )
      })}

      <DimensionChain points={xs} at={H + pad * 0.3} horizontal font={font} />
      {xs.length > 2 && <DimensionChain points={[0, W]} at={H + pad * 0.75} horizontal font={font} />}
      <DimensionChain points={ys} at={W + pad * 0.3} font={font} />
      {ys.length > 2 && <DimensionChain points={[0, H]} at={W + pad * 0.75} font={font} />}
    </svg>
  )
}

function uniqueSorted(values: number[]): number[] {
  return [...new Set(values.map((v) => Math.round(v * 10) / 10))].sort((a, b) => a - b)
}

function OpeningSymbol({ opening, r }: { opening: Opening; r: Rect }) {
  const left = r.x
  const right = r.x + r.width
  const top = r.y
  const bottom = r.y + r.height
  const midX = r.x + r.width / 2
  const midY = r.y + r.height / 2
  const lines: [number, number, number, number, boolean?][] = []

  // The lines meet on the hinge side.
  if (opening === 'turn_left' || opening === 'tilt_turn_left') {
    lines.push([right, top, left, midY], [right, bottom, left, midY])
  }
  if (opening === 'turn_right' || opening === 'tilt_turn_right') {
    lines.push([left, top, right, midY], [left, bottom, right, midY])
  }
  if (opening === 'tilt' || opening.startsWith('tilt_turn')) {
    const dashed = opening !== 'tilt'
    lines.push([left, top, midX, bottom, dashed], [right, top, midX, bottom, dashed])
  }

  if (opening === 'sliding_left' || opening === 'sliding_right') {
    const len = r.width * 0.3
    const dir = opening === 'sliding_left' ? -1 : 1
    const start = midX - (dir * len) / 2
    const end = midX + (dir * len) / 2
    const head = Math.min(r.width, r.height) * 0.06
    return (
      <g className="symbol">
        <line x1={start} y1={midY} x2={end} y2={midY} />
        <polyline points={`${end - dir * head},${midY - head} ${end},${midY} ${end - dir * head},${midY + head}`} />
      </g>
    )
  }

  return (
    <g className="symbol">
      {lines.map(([x1, y1, x2, y2, dashed], i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} className={dashed ? 'dashed' : undefined} />
      ))}
    </g>
  )
}

function DimensionChain(props: { points: number[]; at: number; horizontal?: boolean; font: number }) {
  const { points, at, horizontal, font } = props
  const tick = font * 0.5
  const parts = points.slice(1).map((p, i) => [points[i], p] as const)
  return (
    <g className="dimension">
      {horizontal ? (
        <line x1={points[0]} y1={at} x2={points.at(-1)} y2={at} />
      ) : (
        <line x1={at} y1={points[0]} x2={at} y2={points.at(-1)} />
      )}
      {points.map((p) =>
        horizontal ? (
          <line key={p} x1={p} y1={at - tick} x2={p} y2={at + tick} />
        ) : (
          <line key={p} x1={at - tick} y1={p} x2={at + tick} y2={p} />
        ),
      )}
      {parts.map(([a, b]) =>
        horizontal ? (
          <text key={a} x={(a + b) / 2} y={at - tick * 1.4} textAnchor="middle">
            {fmt(b - a)}
          </text>
        ) : (
          <text
            key={a}
            x={at - tick * 1.4}
            y={(a + b) / 2}
            textAnchor="middle"
            transform={`rotate(-90 ${at - tick * 1.4} ${(a + b) / 2})`}
          >
            {fmt(b - a)}
          </text>
        ),
      )}
    </g>
  )
}
