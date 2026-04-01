import { useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../api'

export default function Sources() {
  const { data, loading, refetch } = useFetch(api.getSources)
  const { data: approved } = useFetch(api.getApprovedSources)
  const [ingestLoading, setIngestLoading] = useState(false)
  const [ingestResult, setIngestResult] = useState(null)
  const [cleanupResult, setCleanupResult] = useState(null)

  const handleIngestAll = async () => {
    if (!approved?.all_urls) return
    setIngestLoading(true)
    setIngestResult(null)
    try {
      const res = await api.ingestBulk(approved.all_urls)
      setIngestResult(res)
      refetch()
    } catch (e) {
      setIngestResult({ error: e.message })
    } finally {
      setIngestLoading(false)
    }
  }

  const handleCleanup = async () => {
    if (!confirm('Удалить все российские источники и их документы?')) return
    try {
      const res = await api.cleanupRussian()
      setCleanupResult(res)
      refetch()
    } catch (e) {
      setCleanupResult({ error: e.message })
    }
  }

  const sources = data?.items || []
  const russianCount = sources.filter(s => s.is_russian).length

  return (
    <div className="page-fade" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Actions */}
      <div className="card" style={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={handleIngestAll}
            disabled={ingestLoading}
            style={{
              padding: '9px 20px', borderRadius: 8, cursor: 'pointer',
              background: 'var(--accent)', border: 'none',
              color: 'white', fontSize: 13, fontWeight: 600,
              opacity: ingestLoading ? 0.6 : 1,
              boxShadow: '0 0 20px rgba(59,130,246,0.3)',
            }}
          >
            {ingestLoading ? '⟳ Загрузка...' : '↓ Загрузить все источники'}
          </button>

          {russianCount > 0 && (
            <button
              onClick={handleCleanup}
              style={{
                padding: '9px 20px', borderRadius: 8, cursor: 'pointer',
                background: 'var(--negative-bg)', border: '1px solid var(--negative)',
                color: 'var(--negative)', fontSize: 13, fontWeight: 600,
              }}
            >
              ✕ Удалить российские ({russianCount})
            </button>
          )}

          <div style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
            {sources.length} источников в БД
          </div>
        </div>

        {ingestResult && !ingestResult.error && (
          <div style={{
            marginTop: 12, padding: '10px 14px',
            background: 'var(--positive-bg)', borderRadius: 6,
            fontSize: 13, color: 'var(--positive)',
          }}>
            ✓ Добавлено: {ingestResult.total_inserted} · Пропущено: {ingestResult.total_skipped} · Ошибок: {ingestResult.total_errors}
          </div>
        )}

        {cleanupResult && !cleanupResult.error && (
          <div style={{
            marginTop: 12, padding: '10px 14px',
            background: 'var(--positive-bg)', borderRadius: 6,
            fontSize: 13, color: 'var(--positive)',
          }}>
            ✓ {cleanupResult.message}
          </div>
        )}
      </div>

      {/* Sources table */}
      {loading ? (
        <div className="loading-state"><div className="spinner" /><span>Загрузка...</span></div>
      ) : (
        <div className="card">
          <div className="card-title">Источники в базе данных</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Источник</th>
                <th>URL</th>
                <th>Документов</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {sources.map(s => (
                <tr key={s.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>#{s.id}</td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{s.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <a href={s.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-hover)', textDecoration: 'none' }}>
                      {s.url}
                    </a>
                  </td>
                  <td style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--accent-hover)' }}>
                    {s.documents_count}
                  </td>
                  <td>
                    {s.is_russian ? (
                      <span className="badge badge-negative">Российский</span>
                    ) : (
                      <span className="badge badge-positive">Одобрен</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Approved sources */}
      {approved?.categories && (
        <div className="card">
          <div className="card-title">Реестр одобренных источников</div>
          {Object.entries(approved.categories).map(([cat, items]) => (
            <div key={cat} style={{ marginBottom: 20 }}>
              <div style={{
                fontSize: 11, fontWeight: 600, color: 'var(--accent)',
                textTransform: 'uppercase', letterSpacing: '0.8px',
                marginBottom: 8, fontFamily: 'var(--font-mono)',
              }}>
                {cat === 'KAZAKHSTAN' ? '🇰🇿 Казахстан'
                  : cat === 'CENTRAL_ASIA' ? '🌏 Центральная Азия'
                  : cat === 'GLOBAL_EN' ? '🌐 Глобальные'
                  : '💬 Социальные'}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {items.map(s => (
                  <div key={s.url} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 12px', background: 'var(--bg-surface)',
                    borderRadius: 6, border: '1px solid var(--border)',
                  }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{s.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.description}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{
                        fontSize: 10, fontFamily: 'var(--font-mono)',
                        padding: '2px 6px', borderRadius: 4,
                        background: s.language === 'ru' ? 'rgba(59,130,246,0.1)' : 'rgba(16,185,129,0.1)',
                        color: s.language === 'ru' ? 'var(--accent-hover)' : 'var(--positive)',
                      }}>
                        {s.language.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
