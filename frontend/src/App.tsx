import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, type Row } from './api'
import { CATALOGS, DEFAULTS, toPayload, type CatalogConfig, type Field } from './catalog'
import { LangContext, useT, type Lang } from './i18n'

export default function App() {
  const [lang, setLang] = useState<Lang>(() =>
    localStorage.getItem('lang') === 'ar' ? 'ar' : 'en',
  )
  const [tab, setTab] = useState(0)

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    localStorage.setItem('lang', lang)
  }, [lang])

  return (
    <LangContext.Provider value={lang}>
      <Header onToggle={() => setLang(lang === 'en' ? 'ar' : 'en')} />
      <nav className="tabs">
        {CATALOGS.map((c, i) => (
          <TabButton key={c.resource} config={c} active={i === tab} onClick={() => setTab(i)} />
        ))}
      </nav>
      <main>
        <CatalogPage key={CATALOGS[tab].resource} config={CATALOGS[tab]} />
      </main>
    </LangContext.Provider>
  )
}

function Header({ onToggle }: { onToggle: () => void }) {
  const { t } = useT()
  return (
    <header>
      <div>
        <h1>{t('app.title')}</h1>
        <p className="muted">{t('app.subtitle')}</p>
      </div>
      <button onClick={onToggle}>{t('lang.switch')}</button>
    </header>
  )
}

function TabButton(props: { config: CatalogConfig; active: boolean; onClick: () => void }) {
  const { t } = useT()
  return (
    <button className={props.active ? 'tab active' : 'tab'} onClick={props.onClick}>
      {t(props.config.tab)}
    </button>
  )
}

function CatalogPage({ config }: { config: CatalogConfig }) {
  const { t, lang } = useT()
  const [rows, setRows] = useState<Row[] | null>(null)
  const [systems, setSystems] = useState<Row[]>([])
  const [q, setQ] = useState('')
  const [systemFilter, setSystemFilter] = useState('')
  const [editing, setEditing] = useState<Row | 'new' | null>(null)
  const [selected, setSelected] = useState<Row | null>(null)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    api
      .list(config.resource, { q, system_id: systemFilter })
      .then(setRows)
      .catch((e: Error) => setError(e.message))
  }, [config.resource, q, systemFilter])

  useEffect(load, [load])
  useEffect(() => {
    api.list('systems').then(setSystems).catch(() => setSystems([]))
  }, [])

  const systemName = (id: unknown) => {
    const s = systems.find((s) => s.id === id)
    return s ? String(s.code) : t('common.none')
  }

  const show = (field: string, row: Row) => {
    const value = row[field]
    if (value === null || value === undefined || value === '') return t('common.none')
    if (field === 'system_id') return systemName(value)
    if (field === 'thermal_break') return t(value ? 'common.yes' : 'common.no')
    if (field === 'role' || field === 'category' || field === 'unit') return t(`${field}.${value}`)
    return String(value)
  }

  const remove = async (row: Row) => {
    if (!confirm(t('confirm.delete'))) return
    try {
      await api.remove(config.resource, row.id)
      if (selected?.id === row.id) setSelected(null)
      load()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <section>
      <div className="toolbar">
        <input
          type="search"
          placeholder={t('action.search')}
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {config.filterBySystem && (
          <select value={systemFilter} onChange={(e) => setSystemFilter(e.target.value)}>
            <option value="">{t('common.allSystems')}</option>
            {systems.map((s) => (
              <option key={s.id} value={s.id}>
                {String(s.code)}
              </option>
            ))}
          </select>
        )}
        <button className="primary" onClick={() => setEditing('new')}>
          {t('action.add')}
        </button>
      </div>

      {error && (
        <p className="error" onClick={() => setError('')}>
          {error}
        </p>
      )}

      {editing && (
        <ItemForm
          config={config}
          systems={systems}
          initial={editing === 'new' ? null : editing}
          onCancel={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}

      {rows === null ? (
        <p className="muted">{t('common.loading')}</p>
      ) : rows.length === 0 ? (
        <p className="muted">{t('common.empty')}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t(`field.${config.codeKey}`)}</th>
                <th>{t('common.name')}</th>
                {config.columns.map((c) => (
                  <th key={c}>{t(`field.${c}`)}</th>
                ))}
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.id}
                  className={selected?.id === row.id ? 'selected' : ''}
                  onClick={() => setSelected(row)}
                >
                  <td className="code">
                    <bdi dir="ltr">{String(row[config.codeKey])}</bdi>
                  </td>
                  <td>{String(row[lang === 'ar' ? 'name_ar' : 'name_en'])}</td>
                  {config.columns.map((c) => (
                    <td key={c}>
                      <bdi dir={c === 'build_up' ? 'ltr' : undefined}>{show(c, row)}</bdi>
                    </td>
                  ))}
                  <td onClick={(e) => e.stopPropagation()}>
                    <div className="actions">
                      <button onClick={() => setEditing(row)}>{t('action.edit')}</button>
                      <button className="danger" onClick={() => remove(row)}>
                        {t('action.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && config.resource === 'profiles' && <ProfileCalculator profile={selected} />}
      {selected && config.resource === 'glass' && <GlassCalculator glass={selected} />}
    </section>
  )
}

function ItemForm(props: {
  config: CatalogConfig
  systems: Row[]
  initial: Row | null
  onCancel: () => void
  onSaved: () => void
}) {
  const { t } = useT()
  const { config } = props
  const [form, setForm] = useState<Record<string, unknown>>(() => {
    const start: Record<string, unknown> = {}
    for (const f of config.fields) {
      start[f.key] = props.initial?.[f.key] ?? DEFAULTS[f.key] ?? ''
    }
    return start
  })
  const [error, setError] = useState('')

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    const payload = toPayload(config.fields, form)
    try {
      if (props.initial) await api.update(config.resource, props.initial.id, payload)
      else await api.create(config.resource, payload)
      props.onSaved()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      {config.fields.map((f) => (
        <label key={f.key} className={f.type === 'checkbox' ? 'check' : ''}>
          <span>{t(`field.${f.key}`)}</span>
          <FieldInput
            field={f}
            systems={props.systems}
            value={form[f.key]}
            onChange={(v) => setForm({ ...form, [f.key]: v })}
          />
        </label>
      ))}
      {error && <p className="error">{error}</p>}
      <div className="form-actions">
        <button type="submit" className="primary">
          {t('action.save')}
        </button>
        <button type="button" onClick={props.onCancel}>
          {t('action.cancel')}
        </button>
      </div>
    </form>
  )
}

function FieldInput(props: {
  field: Field
  systems: Row[]
  value: unknown
  onChange: (value: unknown) => void
}) {
  const { t } = useT()
  const { field, value, onChange } = props
  if (field.type === 'checkbox') {
    return <input type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} />
  }
  if (field.type === 'select' || field.type === 'system') {
    const options =
      field.type === 'system'
        ? props.systems.map((s) => ({ value: String(s.id), label: String(s.code) }))
        : (field.options ?? []).map((o) => ({ value: o, label: t(`${field.optionPrefix}.${o}`) }))
    return (
      <select required={field.required} value={String(value ?? '')} onChange={(e) => onChange(e.target.value)}>
        {!field.required || value === '' ? <option value="">{t('common.none')}</option> : null}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    )
  }
  return (
    <input
      type={field.type}
      step={field.step}
      min={field.type === 'number' ? 0 : undefined}
      required={field.required}
      dir={field.key === 'name_ar' ? 'rtl' : field.key === 'name_en' ? 'ltr' : undefined}
      value={String(value ?? '')}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

function ProfileCalculator({ profile }: { profile: Row }) {
  const { t } = useT()
  const [length, setLength] = useState('1000')
  const [result, setResult] = useState<{ weight_kg: number; price: number | null } | null>(null)
  const [error, setError] = useState('')

  const run = (e: FormEvent) => {
    e.preventDefault()
    setError('')
    api.profilePiece(profile.id, Number(length)).then(setResult).catch((err: Error) => setError(err.message))
  }

  return (
    <form className="card calc" onSubmit={run}>
      <h3>
        {t('calc.profileTitle')} · {String(profile.article_no)}
      </h3>
      <label>
        <span>{t('calc.length')}</span>
        <input type="number" min="1" step="0.1" required value={length} onChange={(e) => setLength(e.target.value)} />
      </label>
      <button type="submit" className="primary">
        {t('action.calculate')}
      </button>
      {result && (
        <p className="result">
          {t('calc.weight')}: <b>{result.weight_kg} kg</b>
          {result.price !== null && (
            <>
              {' · '}
              {t('calc.price')}: <b>{result.price}</b>
            </>
          )}
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function GlassCalculator({ glass }: { glass: Row }) {
  const { t } = useT()
  const [width, setWidth] = useState('1000')
  const [height, setHeight] = useState('1000')
  const [result, setResult] = useState<{ area_m2: number; weight_kg: number; price: number | null } | null>(null)
  const [error, setError] = useState('')

  const run = (e: FormEvent) => {
    e.preventDefault()
    setError('')
    api
      .glassPane(glass.id, Number(width), Number(height))
      .then(setResult)
      .catch((err: Error) => setError(err.message))
  }

  return (
    <form className="card calc" onSubmit={run}>
      <h3>
        {t('calc.glassTitle')} · {String(glass.code)}
      </h3>
      <label>
        <span>{t('calc.width')}</span>
        <input type="number" min="1" required value={width} onChange={(e) => setWidth(e.target.value)} />
      </label>
      <label>
        <span>{t('calc.height')}</span>
        <input type="number" min="1" required value={height} onChange={(e) => setHeight(e.target.value)} />
      </label>
      <button type="submit" className="primary">
        {t('action.calculate')}
      </button>
      {result && (
        <p className="result">
          {t('calc.area')}: <b>{result.area_m2} m²</b> · {t('calc.weight')}: <b>{result.weight_kg} kg</b>
          {result.price !== null && (
            <>
              {' · '}
              {t('calc.price')}: <b>{result.price}</b>
            </>
          )}
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </form>
  )
}
