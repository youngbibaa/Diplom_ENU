import { useState, useMemo } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../api'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, BarChart, Bar, Cell
} from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12, minWidth: 160,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 3 }}>
          <span style={{ color: p.color }}>● {p.name}</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function Trends() {
  const { data: trends, loading } = useFetch(api.getTopTrends)
  const { data: topics } = useFetch(api.getTopics)
  const [metric, setMetric] = useState('mentions_count')
  const [selectedTopics, setSelectedTopics] = useState(new Set())

  const topicNames = useMemo(() => {
    if (!topics) return {}
    return Object.fromEntries(topics.map(t => [t.topic_id, t.name]))
  }, [topics])

  // Build timeline grouped by date × topic
  const { timelineData, allTopicIds } = useMemo(() => {
    if (!trends) return { timelineData: [], allTopicIds: [] }
    const byDate = {}
    const topicIds = new Set()
    trends.forEach(t => {
      if (!byDate[t.date]) byDate[t.date] = { date: t.date }
      byDate[t.date][t.topic_id] = t[metric]
      topicIds.add(t.topic_id)
    })
    const sorted = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))
    return { timelineData: sorted, allTopicIds: [...topicIds] }
  }, [trends, metric])

  const visibleTopics = selectedTopics.size > 0 ? [...selectedTopics] : allTopicIds.slice(0, 5)

  // Top trends bar data
  const barData = useMemo(() => {
    if (!trends) return []
    const byTopic = {}
    trends.forEach(t => {
      if (!byTopic[t.topic_id] || byTopic[t.topic_id].trend_score < t.trend_score) {
        byTopic[t.topic_id] = t
      }
    })
    return Object.values(byTopic)
      .sort((a, b) => b.trend_score - a.trend_score)
      .slice(0, 8)
  }, [trends])

  const toggleTopic = (id) => {
    setSelectedTopics(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  if (loading) return (
    <div className="loading-state"><div className="spinner" /><span>Загрузка трендов...</span></div>
  )

  return (
    <div className="page-fade" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Top bar chart */}
      <div className="card">
        <div className="card-title">Рейтинг тем по Trend Score</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData} margin={{ top: 5, right: 5, bottom: 40, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="topic_name"
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              axisLine={false} tickLine={false}
              angle={-20} textAnchor="end" height={60}
              tickFormatter={v => v.length > 22 ? v.slice(0, 22) + '…' : v}
            />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="trend_score" name="Trend Score" radius={[4, 4, 0, 0]}>
              {barData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Timeline */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Временная динамика</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { key: 'mentions_count', label: 'Упоминания' },
              { key: 'trend_score', label: 'Score' },
              { key: 'sentiment_avg', label: 'Тональность' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setMetric(key)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 6,
                  border: `1px solid ${metric === key ? 'var(--accent)' : 'var(--border)'}`,
                  background: metric === key ? 'var(--accent-glow)' : 'transparent',
                  color: metric === key ? 'var(--accent-hover)' : 'var(--text-muted)',
                  fontSize: 12, fontWeight: 500, cursor: 'pointer',
                }}
              >{label}</button>
            ))}
          </div>
        </div>

        {/* Topic filter chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
          {allTopicIds.map((id, i) => {
            const active = selectedTopics.size === 0 ? i < 5 : selectedTopics.has(id)
            return (
              <button
                key={id}
                onClick={() => toggleTopic(id)}
                style={{
                  padding: '3px 10px',
                  borderRadius: 20,
                  border: `1px solid ${active ? COLORS[i % COLORS.length] : 'var(--border)'}`,
                  background: active ? `${COLORS[i % COLORS.length]}18` : 'transparent',
                  color: active ? COLORS[i % COLORS.length] : 'var(--text-muted)',
                  fontSize: 11, cursor: 'pointer',
                }}
              >
                {topicNames[id] || `#${id}`}
              </button>
            )
          })}
        </div>

        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={timelineData} margin={{ top: 5, right: 5, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
              axisLine={false} tickLine={false}
              tickFormatter={d => d.slice(5)}
            />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            {visibleTopics.map((id, i) => (
              <Line
                key={id}
                type="monotone"
                dataKey={id}
                name={topicNames[id] || `#${id}`}
                stroke={COLORS[allTopicIds.indexOf(id) % COLORS.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed table */}
      <div className="card">
        <div className="card-title">Детальные данные</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Тема</th>
              <th>Дата</th>
              <th>Упоминания</th>
              <th>Рост</th>
              <th>Тональность</th>
              <th>Trend Score</th>
            </tr>
          </thead>
          <tbody>
            {(trends || []).slice(0, 20).map((t, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 500, color: 'var(--text-primary)', maxWidth: 200 }}>
                  {t.topic_name}
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
                  <span className={`badge badge-${t.sentiment_avg > 0.05 ? 'positive' : t.sentiment_avg < -0.05 ? 'negative' : 'neutral'}`}>
                    {t.sentiment_avg > 0 ? '+' : ''}{t.sentiment_avg?.toFixed(3)}
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
      </div>
    </div>
  )
}
