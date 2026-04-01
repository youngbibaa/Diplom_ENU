import { useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../api'

const SENTIMENT_LABELS = { positive: 'Позитивные', neutral: 'Нейтральные', negative: 'Негативные' }

export default function Documents() {
  const [topicId, setTopicId] = useState('')
  const [sentimentLabel, setSentimentLabel] = useState('')
  const [offset, setOffset] = useState(0)
  const limit = 15

  const { data: topics } = useFetch(api.getTopics)
  const { data, loading, refetch } = useFetch(
    () => api.getDocuments({ limit, offset, topic_id: topicId || undefined, sentiment_label: sentimentLabel || undefined }),
    [topicId, sentimentLabel, offset]
  )

  const docs = data?.items || []
  const total = data?.total || 0
  const pages = Math.ceil(total / limit)
  const currentPage = Math.floor(offset / limit) + 1

  const resetFilters = () => {
    setTopicId(''); setSentimentLabel(''); setOffset(0)
  }

  return (
    <div className="page-fade" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Filters */}
      <div className="card" style={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 180 }}>
            <select
              value={topicId}
              onChange={e => { setTopicId(e.target.value); setOffset(0) }}
              style={{
                width: '100%', padding: '8px 12px',
                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                borderRadius: 6, color: 'var(--text-secondary)', fontSize: 13,
              }}
            >
              <option value="">Все темы</option>
              {(topics || []).map(t => (
                <option key={t.topic_id} value={t.topic_id}>{t.name}</option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={sentimentLabel}
              onChange={e => { setSentimentLabel(e.target.value); setOffset(0) }}
              style={{
                padding: '8px 12px',
                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                borderRadius: 6, color: 'var(--text-secondary)', fontSize: 13,
              }}
            >
              <option value="">Любая тональность</option>
              <option value="positive">Позитивные</option>
              <option value="neutral">Нейтральные</option>
              <option value="negative">Негативные</option>
            </select>
          </div>

          {(topicId || sentimentLabel) && (
            <button
              onClick={resetFilters}
              style={{
                padding: '8px 14px', borderRadius: 6,
                border: '1px solid var(--border)', background: 'transparent',
                color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer',
              }}
            >✕ Сбросить</button>
          )}

          <div style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
            {total.toLocaleString('ru')} документов
          </div>
        </div>
      </div>

      {/* Documents */}
      {loading ? (
        <div className="loading-state"><div className="spinner" /><span>Загрузка документов...</span></div>
      ) : docs.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">▤</div>
          <div className="empty-state-text">Документы не найдены</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {docs.map(doc => (
            <div
              key={doc.id}
              className="card"
              style={{ padding: '18px 22px', transition: 'all 0.15s' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', textDecoration: 'none' }}
                    onMouseEnter={e => e.target.style.color = 'var(--accent-hover)'}
                    onMouseLeave={e => e.target.style.color = 'var(--text-primary)'}
                  >
                    {doc.title}
                  </a>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', flexShrink: 0 }}>
                  {doc.sentiment && (
                    <span className={`badge badge-${doc.sentiment.label}`}>
                      {doc.sentiment.label === 'positive' ? '↑' : doc.sentiment.label === 'negative' ? '↓' : '→'}
                      {' '}{doc.sentiment.score > 0 ? '+' : ''}{doc.sentiment.score?.toFixed(3)}
                    </span>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
                {doc.published_at && (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    📅 {new Date(doc.published_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                )}
                {doc.author && (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>✍ {doc.author}</span>
                )}
                {doc.topic && (
                  <span style={{
                    fontSize: 12, color: 'var(--accent-hover)',
                    background: 'var(--accent-glow)',
                    padding: '1px 8px', borderRadius: 10,
                  }}>
                    ◉ {doc.topic.topic_name}
                  </span>
                )}
              </div>

              {doc.text_clean && (
                <div style={{
                  marginTop: 10, fontSize: 12, color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)', lineHeight: 1.5,
                  overflow: 'hidden', display: '-webkit-box',
                  WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                }}>
                  {doc.text_clean.slice(0, 200)}…
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '8px 0' }}>
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
            style={{
              padding: '7px 16px', borderRadius: 6, cursor: 'pointer',
              border: '1px solid var(--border)', background: 'var(--bg-card)',
              color: offset === 0 ? 'var(--text-muted)' : 'var(--text-primary)', fontSize: 13,
            }}
          >← Назад</button>

          <span style={{ padding: '7px 14px', fontSize: 13, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {currentPage} / {pages}
          </span>

          <button
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= total}
            style={{
              padding: '7px 16px', borderRadius: 6, cursor: 'pointer',
              border: '1px solid var(--border)', background: 'var(--bg-card)',
              color: offset + limit >= total ? 'var(--text-muted)' : 'var(--text-primary)', fontSize: 13,
            }}
          >Вперёд →</button>
        </div>
      )}
    </div>
  )
}
