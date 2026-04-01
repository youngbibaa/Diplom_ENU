import { useFetch } from '../hooks/useFetch'
import { api } from '../api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts'

const SENTIMENT_COLORS = {
  positive: '#10b981',
  neutral: '#f59e0b',
  negative: '#ef4444',
}

const SENTIMENT_LABELS = {
  positive: 'Позитивные',
  neutral: 'Нейтральные',
  negative: 'Негативные',
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-light)',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
          {p.name}: <strong>{p.value}</strong>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const { data: summary, loading } = useFetch(api.getDashboardSummary)
  const { data: trends } = useFetch(api.getTopTrends)

  // Build timeline data from top trends
  const timelineData = (() => {
    if (!trends) return []
    const byDate = {}
    trends.slice(0, 40).forEach(t => {
      const d = t.date
      if (!byDate[d]) byDate[d] = { date: d, упоминания: 0, score: 0 }
      byDate[d].упоминания += t.mentions_count
      byDate[d].score = Math.max(byDate[d].score, t.trend_score)
    })
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date)).slice(-14)
  })()

  if (loading) return (
    <div className="loading-state">
      <div className="spinner" />
      <span>Загрузка данных...</span>
    </div>
  )

  const s = summary || {}
  const sentItems = s.sentiment_summary || []
  const topTrends = (s.top_trends || []).slice(0, 5)

  return (
    <div className="page-fade">
      {/* Stats */}
      <div className="stats-grid">
        {[
          { label: 'Документов', value: s.total_documents?.toLocaleString('ru') ?? '—', meta: 'в базе данных' },
          { label: 'Тем', value: s.total_topics ?? '—', meta: 'выявлено LDA' },
          { label: 'Источников', value: s.total_sources ?? '—', meta: 'активных RSS' },
          {
            label: 'Ср. тональность',
            value: s.overall_avg_score != null
              ? (s.overall_avg_score > 0 ? '+' : '') + s.overall_avg_score.toFixed(3)
              : '—',
            meta: s.overall_avg_score > 0 ? 'позитивный фон' : s.overall_avg_score < 0 ? 'негативный фон' : 'нейтральный фон',
          },
        ].map(({ label, value, meta }) => (
          <div className="stat-card" key={label}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
            <div className="stat-meta">{meta}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="charts-grid">
        {/* Timeline */}
        <div className="card">
          <div className="card-title">Активность по датам</div>
          {timelineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={timelineData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                  axisLine={false} tickLine={false}
                  tickFormatter={d => d.slice(5)}
                />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone" dataKey="упоминания"
                  stroke="#3b82f6" strokeWidth={2}
                  fill="url(#areaGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">◌</div>
              <div className="empty-state-text">Нет данных о трендах</div>
            </div>
          )}
        </div>

        {/* Sentiment */}
        <div className="card">
          <div className="card-title">Тональность</div>
          {sentItems.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
              {sentItems.map(item => (
                <div key={item.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span className={`badge badge-${item.label}`}>
                      {SENTIMENT_LABELS[item.label] || item.label}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)' }}>
                      {item.count} ({(item.share * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="score-bar-track">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${item.share * 100}%`,
                        background: SENTIMENT_COLORS[item.label] || 'var(--accent)',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-text">Нет данных</div>
            </div>
          )}
        </div>
      </div>

      {/* Top trends table */}
      <div className="card">
        <div className="card-title">Топ трендов сегодня</div>
        {topTrends.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Тема</th>
                <th>Дата</th>
                <th>Упоминаний</th>
                <th>Рост</th>
                <th>Trend Score</th>
              </tr>
            </thead>
            <tbody>
              {topTrends.map(t => (
                <tr key={`${t.topic_id}-${t.date}`}>
                  <td>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 13 }}>
                      {t.topic_name}
                    </div>
                    <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginTop: 2 }}>
                      {t.keywords}
                    </div>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{t.date}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-hover)' }}>
                    {t.mentions_count}
                  </td>
                  <td>
                    <span className={`trend-chip ${t.growth_rate > 0 ? 'trend-up' : t.growth_rate < 0 ? 'trend-down' : 'trend-flat'}`}>
                      {t.growth_rate > 0 ? '↑' : t.growth_rate < 0 ? '↓' : '→'}
                      {' '}{Math.abs(t.growth_rate * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <div className="score-bar-wrap">
                      <div className="score-bar-track">
                        <div className="score-bar-fill" style={{ width: `${Math.min(t.trend_score / 80 * 100, 100)}%` }} />
                      </div>
                      <span className="score-val">{t.trend_score?.toFixed(1)}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">◌</div>
            <div className="empty-state-text">Нет данных о трендах. Запустите аналитику.</div>
          </div>
        )}
      </div>
    </div>
  )
}
