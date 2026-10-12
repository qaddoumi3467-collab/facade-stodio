import { useEffect, useState } from 'react'
import { api, ApiError, type Calculation, type ElementData, type Row, type SavedElement } from './api'
import { defaultProfiles, newElement, PROFILE_CHOICES, type Catalog } from './elements'
import { Drawing } from './Drawing'
import { useT } from './i18n'
import {
  getNode,
  OPENINGS,
  normalizeNumber,
  parseSize,
  pathKey,
  removeSplit,
  setSizes,
  splitField,
  updateField,
  type Direction,
  type Opening,
  type Path,
  type SplitNode,
} from './layout'

export function DesignerPage() {
  const { t } = useT()
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [elements, setElements] = useState<SavedElement[]>([])
  const [draft, setDraft] = useState<ElementData | null>(null)
  const [savedId, setSavedId] = useState<number | null>(null)
  const [dirty, setDirty] = useState(false)
  const [selected, setSelected] = useState<Path | null>(null)
  const [calc, setCalc] = useState<Calculation | null>(null)
  const [calcError, setCalcError] = useState<Error | null>(null)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    Promise.all([api.list('systems'), api.list('profiles'), api.list('glass'), api.elements()])
      .then(([systems, profiles, glass, saved]) => {
        const cat = { systems, profiles, glass }
        setCatalog(cat)
        setElements(saved)
        if (saved.length > 0) open(saved[0])
        else setDraft(newElement(cat, t('designer.newName')))
      })
      .catch(setError)
    // Load once; `open` and `t` only matter for the first element.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recalculate the drawing and lists shortly after each change.
  useEffect(() => {
    if (!draft) return
    const controller = new AbortController()
    const timer = setTimeout(() => {
      api
        .calculateElement(draft, controller.signal)
        .then((result) => {
          setCalc(result)
          setCalcError(null)
        })
        .catch((e: Error) => {
          if (e.name !== 'AbortError') setCalcError(e)
        })
    }, 250)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [draft])

  const change = (patch: Partial<ElementData>) => {
    if (!draft) return
    setDraft({ ...draft, ...patch })
    setDirty(true)
  }

  const discardOk = () => !dirty || confirm(t('designer.discard'))

  function open(element: SavedElement) {
    const { id, ...data } = element
    const clean: ElementData & Record<string, unknown> = { ...data }
    delete clean.created_at
    delete clean.updated_at
    setDraft(clean)
    setSavedId(id)
    setDirty(false)
    setSelected(null)
    setCalc(null)
  }

  const startNew = () => {
    if (!catalog || !discardOk()) return
    setDraft(newElement(catalog, t('designer.newName'), draft?.system_id))
    setSavedId(null)
    setDirty(false)
    setSelected(null)
    setCalc(null)
  }

  const save = async () => {
    if (!draft) return
    try {
      const saved = await api.saveElement(draft, savedId ?? undefined)
      setSavedId(saved.id)
      setDirty(false)
      setError(null)
      setElements(await api.elements())
    } catch (e) {
      setError(e as Error)
    }
  }

  const remove = async () => {
    if (savedId === null || !catalog || !confirm(t('designer.confirmDelete'))) return
    try {
      await api.deleteElement(savedId)
      const rest = await api.elements()
      setElements(rest)
      setDirty(false)
      if (rest.length > 0) open(rest[0])
      else {
        setDraft(newElement(catalog, t('designer.newName')))
        setSavedId(null)
      }
    } catch (e) {
      setError(e as Error)
    }
  }

  const message = (e: Error) => {
    const code = e instanceof ApiError ? e.code : undefined
    const key = `error.${code}`
    return code && t(key) !== key ? t(key) : e.message
  }

  if (error && !catalog) return <p className="error">{message(error)}</p>
  if (!catalog) return <p className="muted">{t('common.loading')}</p>
  if (!draft) return <p className="muted">{t('designer.noCatalog')}</p>

  return (
    <div className="designer">
      <aside className="element-list">
        <button className="primary" onClick={startNew}>
          {t('designer.new')}
        </button>
        <ul>
          {elements.map((e) => (
            <li key={e.id}>
              <button
                className={e.id === savedId ? 'active' : ''}
                onClick={() => e.id !== savedId && discardOk() && open(e)}
              >
                <b>{e.position || '·'}</b> {e.name}
                <small className="muted">
                  <bdi dir="ltr">
                    {e.width_mm} × {e.height_mm}
                  </bdi>
                  {e.quantity > 1 && ` · ×${e.quantity}`}
                </small>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className="designer-main">
        <ElementForm catalog={catalog} draft={draft} onChange={change} />

        <div className="toolbar">
          <button className="primary" onClick={save}>
            {t('action.save')}
          </button>
          {savedId !== null && (
            <button className="danger" onClick={remove}>
              {t('action.delete')}
            </button>
          )}
          <span className="muted status">{dirty || savedId === null ? t('designer.unsaved') : t('designer.saved')}</span>
        </div>
        {error && (
          <p className="error" onClick={() => setError(null)}>
            {message(error)}
          </p>
        )}

        <div className="drawing-row">
          <div className="drawing-wrap">
            {calc ? (
              <Drawing geometry={calc.geometry} selected={selected} onSelect={setSelected} stale={Boolean(calcError)} />
            ) : (
              !calcError && <p className="muted">{t('common.loading')}</p>
            )}
            {calcError && <p className="error">{message(calcError)}</p>}
          </div>
          <FieldPanel
            catalog={catalog}
            draft={draft}
            path={selected}
            onLayout={(layout, select) => {
              change({ layout })
              if (select !== undefined) setSelected(select)
            }}
          />
        </div>

        {calc && <PartLists calc={calc} quantity={draft.quantity} />}
      </div>
    </div>
  )
}

function ElementForm(props: { catalog: Catalog; draft: ElementData; onChange: (patch: Partial<ElementData>) => void }) {
  const { t, lang } = useT()
  const { catalog, draft, onChange } = props
  const name = (row: Row) => String(row[lang === 'ar' ? 'name_ar' : 'name_en'])

  return (
    <div className="card form">
      <label>
        <span>{t('designer.position')}</span>
        <input value={draft.position} maxLength={64} onChange={(e) => onChange({ position: e.target.value })} />
      </label>
      <label>
        <span>{t('designer.name')}</span>
        <input value={draft.name} maxLength={200} onChange={(e) => onChange({ name: e.target.value })} />
      </label>
      <label>
        <span>{t('designer.quantity')}</span>
        <NumberBox value={draft.quantity} onChange={(v) => v !== null && v >= 1 && onChange({ quantity: Math.round(v) })} />
      </label>
      <label>
        <span>{t('designer.width')}</span>
        <NumberBox value={draft.width_mm} onChange={(v) => v !== null && v > 0 && onChange({ width_mm: v })} />
      </label>
      <label>
        <span>{t('designer.height')}</span>
        <NumberBox value={draft.height_mm} onChange={(v) => v !== null && v > 0 && onChange({ height_mm: v })} />
      </label>
      <label>
        <span>{t('designer.system')}</span>
        <select
          value={draft.system_id}
          onChange={(e) => {
            const systemId = Number(e.target.value)
            const profiles = defaultProfiles(catalog.profiles, systemId)
            onChange({
              system_id: systemId,
              ...profiles,
              frame_profile_id: profiles.frame_profile_id ?? draft.frame_profile_id,
            })
          }}
        >
          {catalog.systems.map((s) => (
            <option key={s.id} value={s.id}>
              {String(s.code)} · {name(s)}
            </option>
          ))}
        </select>
      </label>
      {PROFILE_CHOICES.map((choice) => (
        <label key={choice.key}>
          <span>{t(choice.label)}</span>
          <select
            value={draft[choice.key] ?? ''}
            onChange={(e) => onChange({ [choice.key]: e.target.value === '' ? null : Number(e.target.value) })}
          >
            {(choice.optional || draft[choice.key] === null) && <option value="">{t('designer.none')}</option>}
            {catalog.profiles
              .filter((p) => p.system_id === draft.system_id && choice.roles.includes(String(p.role)))
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {String(p.article_no)} · {name(p)}
                </option>
              ))}
          </select>
        </label>
      ))}
      <label>
        <span>{t('designer.glass')}</span>
        <select value={draft.glass_id} onChange={(e) => onChange({ glass_id: Number(e.target.value) })}>
          {catalog.glass.map((g) => (
            <option key={g.id} value={g.id}>
              {String(g.code)} · {name(g)}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}

/** A number box that also accepts Arabic digits. Blank gives null. */
function NumberBox(props: { value: number | null; onChange: (value: number | null) => void; placeholder?: string }) {
  const [text, setText] = useState(props.value === null ? '' : String(props.value))
  // Follow outside changes (another element opened, a split resized), but
  // keep what the user is typing when it means the same number.
  const [seen, setSeen] = useState(props.value)
  if (props.value !== seen) {
    setSeen(props.value)
    if (parseSize(text) !== props.value) setText(props.value === null ? '' : String(props.value))
  }
  return (
    <input
      inputMode="decimal"
      dir="ltr"
      value={text}
      placeholder={props.placeholder}
      onChange={(e) => {
        setText(e.target.value)
        const clean = normalizeNumber(e.target.value)
        const value = parseSize(e.target.value)
        if (clean === '' || value !== null) props.onChange(value)
      }}
    />
  )
}

function FieldPanel(props: {
  catalog: Catalog
  draft: ElementData
  path: Path | null
  onLayout: (layout: ElementData['layout'], select?: Path | null) => void
}) {
  const { t, lang } = useT()
  const [parts, setParts] = useState(2)
  const { draft, path, onLayout } = props
  const layout = draft.layout

  let node
  try {
    node = path ? getNode(layout, path) : null
  } catch {
    node = null
  }
  if (!path || !node || node.kind !== 'field') {
    return <div className="card field-panel muted">{t('designer.clickField')}</div>
  }
  const field = node
  const parentPath = path.length > 0 ? path.slice(0, -1) : null
  const parent = parentPath ? (getNode(layout, parentPath) as SplitNode) : null

  const split = (direction: Direction) => {
    const next = splitField(layout, path, direction, parts)
    const sameWay = parent && parent.direction === direction
    onLayout(next, sameWay ? path : [...path, 0])
  }

  return (
    <div className="card field-panel">
      <h3>{t('designer.field')}</h3>
      <label>
        <span>{t('designer.opening')}</span>
        <select value={field.opening} onChange={(e) => onLayout(updateField(layout, path, { opening: e.target.value as Opening }))}>
          {OPENINGS.map((o) => (
            <option key={o} value={o}>
              {t(`opening.${o}`)}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>{t('designer.glass')}</span>
        <select
          value={field.glass_id ?? ''}
          onChange={(e) =>
            onLayout(updateField(layout, path, { glass_id: e.target.value === '' ? null : Number(e.target.value) }))
          }
        >
          <option value="">{t('designer.glassDefault')}</option>
          {props.catalog.glass.map((g) => (
            <option key={g.id} value={g.id}>
              {String(g.code)} · {String(g[lang === 'ar' ? 'name_ar' : 'name_en'])}
            </option>
          ))}
        </select>
      </label>

      <div className="split-row">
        <label>
          <span>{t('designer.parts')}</span>
          <input
            type="number"
            min={2}
            max={20}
            value={parts}
            onChange={(e) => setParts(Math.max(2, Math.min(20, Number(e.target.value) || 2)))}
          />
        </label>
        <button onClick={() => split('vertical')}>{t('designer.splitColumns')}</button>
        <button onClick={() => split('horizontal')}>{t('designer.splitRows')}</button>
      </div>

      {parent && parentPath && (
        <div className="sizes">
          <h3>{t(parent.direction === 'vertical' ? 'designer.sizesColumns' : 'designer.sizesRows')}</h3>
          <div className="size-boxes" dir="ltr">
            {parent.sizes.map((size, i) => (
              <NumberBox
                key={`${pathKey(parentPath)}-${i}-${parent.sizes.length}`}
                value={size}
                placeholder={t('designer.auto')}
                onChange={(v) => {
                  const sizes = parent.sizes.slice()
                  sizes[i] = v
                  onLayout(setSizes(layout, parentPath, sizes))
                }}
              />
            ))}
          </div>
          <p className="muted hint">{t('designer.sizesHint')}</p>
          <button className="danger" onClick={() => onLayout(removeSplit(layout, parentPath), parentPath)}>
            {t('designer.removeSplit')}
          </button>
        </div>
      )}
    </div>
  )
}

const num = (n: number, digits = 1) =>
  n.toLocaleString('en-US', { maximumFractionDigits: digits, useGrouping: false })

function PartLists({ calc, quantity }: { calc: Calculation; quantity: number }) {
  const { t, lang } = useT()
  const name = (row: { name_en: string; name_ar: string }) => (lang === 'ar' ? row.name_ar : row.name_en)
  const price = (p: number | null) => (p === null ? t('common.none') : num(p, 2))
  const totals = calc.totals

  return (
    <div className="part-lists">
      <h3>{t('designer.cutList')}</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t('designer.article')}</th>
              <th>{t('common.name')}</th>
              <th>{t('designer.role')}</th>
              <th>{t('designer.length')}</th>
              <th>{t('designer.cut')}</th>
              <th>{t('designer.qty')}</th>
              <th>{t('designer.weight')}</th>
              <th>{t('designer.price')}</th>
            </tr>
          </thead>
          <tbody>
            {calc.profiles.map((line, i) => (
              <tr key={i}>
                <td className="code">
                  <bdi dir="ltr">{line.article_no}</bdi>
                </td>
                <td>{name(line)}</td>
                <td>{t(`role.${line.role}`)}</td>
                <td>
                  <bdi dir="ltr">{num(line.length_mm)}</bdi>
                </td>
                <td>
                  <bdi dir="ltr">
                    {line.angle_start}° / {line.angle_end}°
                  </bdi>
                </td>
                <td>{line.quantity}</td>
                <td>{num(line.weight_kg, 3)}</td>
                <td>{price(line.price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3>{t('designer.glassList')}</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t('field.code')}</th>
              <th>{t('common.name')}</th>
              <th>{t('designer.size')}</th>
              <th>{t('designer.qty')}</th>
              <th>{t('designer.area')}</th>
              <th>{t('designer.weight')}</th>
              <th>{t('designer.price')}</th>
            </tr>
          </thead>
          <tbody>
            {calc.glass.map((line, i) => (
              <tr key={i}>
                <td className="code">
                  <bdi dir="ltr">{line.code}</bdi>
                </td>
                <td>{name(line)}</td>
                <td>
                  <bdi dir="ltr">
                    {num(line.width_mm)} × {num(line.height_mm)}
                  </bdi>
                </td>
                <td>{line.quantity}</td>
                <td>{num(line.area_m2, 4)}</td>
                <td>{num(line.weight_kg, 3)}</td>
                <td>{price(line.price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="totals">
        {t('designer.totals')}: {t('designer.weight')} <b>{num(totals.weight_kg, 3)}</b> · {t('designer.area')}{' '}
        <b>{num(totals.glass_area_m2, 4)}</b> · {t('designer.price')} <b>{num(totals.price, 2)}</b>
        {quantity > 1 && (
          <>
            <br />
            {t('designer.forQuantity').replace('{n}', String(quantity))}: {t('designer.weight')}{' '}
            <b>{num(totals.weight_kg * quantity, 3)}</b> · {t('designer.price')}{' '}
            <b>{num(totals.price * quantity, 2)}</b>
          </>
        )}
      </p>
      {!totals.price_complete && <p className="muted">{t('designer.priceIncomplete')}</p>}
    </div>
  )
}
