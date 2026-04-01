import { useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../api'

export default function Topics() {
  const { data: topics, loading } = useFetch(api.getTopics)
  const [selected, setSelected] = useState(null)
  const { data: topicDocs, loading: docsLoading } = useFetch(
    () => selected ? api.getTopicDocuments(selected, 8) : Promise.resolve(null),
    [selected]
  )

  if (loading) return (
    <div className="loading-state"><div className="spinner" /><span>Загрузка тем...</span></div>
  )

  const maxCount = Math.max(...(topics || []).map(t => t.documents_count), 1)

  return (
    <div className="page-fade">
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: 16 }}>
        {/* Topics list */}
        <div className="card">
          <div className="card-title">Выявленные темы · {topics?.length ?? 0}</div>
          {(topics || []).map((topic, i) => (
            <div
              key={topic.topic_id}
              className="topic-item"
              style={{ cursor: 'pointer', borderRadius: 6, padding: '14px 8px' }}
              onClick={() => setSelected(selected === topic.topic_id ? null : topic.topic_id)}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 11,
                    color: 'var(--accent)',
                    background: 'var(--accent-glow)',
                    padding: '1px 6px',
                    borderRadius: 4,
                  }}>#{topic.topic_id}</span>
                  <div className="topic-name">{topic.name}</div>
                </div>
                <div className="topic-keywords">{topic.keywords}</div>
                <div className="topic-bar" style={{ width: `${(topic.documents_count / maxCount) * 100}%` }} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginLeft: 16, gap: 4 }}>
                <div className="topic-count">{topic.documents_count}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>документов</div>
              </div>
            </div>
          ))}
        </div>

        {/* Topic documents panel */}
        {selected && (
          <div className="card">
            <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Документы темы</span>
              <button
                onClick={() => setSelected(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}
              >×</button>
            </div>
            {docsLoading ? (
              <div className="loading-state" style={{ padding: 32 }}>
                <div className="spinner" /><span>Загрузка...</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(topicDocs?.items || []).map(doc => (
                  <div key={doc.id} style={{
                    padding: '14px',
                    background: 'var(--bg-surface)',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <a
                        href={doc.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: 13, fontWeight: 500, color: 'var(--accent-hover)', textDecoration: 'none', flex: 1 }}
                      >
                        {doc.title}
                      </a>
                      {doc.sentiment && (
                        <span className={`badge badge-${doc.sentiment.label}`} style={{ flexShrink: 0 }}>
                          {doc.sentiment.label === 'positive' ? '↑' : doc.sentiment.label === 'negative' ? '↓' : '→'}
                          {' '}{doc.sentiment.score > 0 ? '+' : ''}{doc.sentiment.score?.toFixed(2)}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, fontFamily: 'var(--font-mono)' }}>
                      {doc.published_at ? new Date(doc.published_at).toLocaleDateString('ru-RU') : '—'}
                      {' · '}p={doc.topic_probability?.toFixed(2)}
                    </div>
                  </div>
                ))}
                {topicDocs?.total > 8 && (
                  <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', padding: 8 }}>
                    + ещё {topicDocs.total - 8} документов
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
