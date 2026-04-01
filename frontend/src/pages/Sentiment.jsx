import { useFetch } from '../hooks/useFetch'
import { api } from '../api'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = { positive: '#10b981', neutral: '#f59e0b', negative: '#ef4444' }
const LABELS = { positive: 'Позитивные', neutral: 'Нейтральные', negative: 'Негативные' }

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
      borderRadius: 8, padding: '10px 14px', fontSize: 13,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: COLORS[d.label] || 'var(--text-primary)' }}>
        {LABELS[d.label] || d.label}
      </div>
      <div style={{ color: 'var(--text-secondary)' }}>Документов: <strong>{d.count}</strong></div>
      <div style={{ color: 'var(--text-secondary)' }}>Доля: <strong>{(d.share * 100).toFixed(1)}%</strong></div>
      <div style={{ color: 'var(--text-secondary)' }}>Ср. score: <strong>{d.avg_score?.toFixed(3)}</strong></div>
    </div>
  )
}

export default function Sentiment() {
  const { data, loading } = useFetch(api.getSentimentSummary)

  if (loading) return (
    <div className="loading-state"><div className="spinner" /><span>Загрузка...</span></div>
  )

  const items = data?.items || []
  const pieData = items.map(i => ({ ...i, value: i.count, name: LABELS[i.label] || i.label }))

  return (
    <div className="page-fade" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* KPI row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Всего документов</div>
          <div className="stat-value">{data?.total_documents?.toLocaleString('ru') ?? '—'}</div>
          <div className="stat-meta">в базе данных</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Средний score</div>
          <div className="stat-value" style={{ color: data?.overall_avg_score > 0 ? 'var(--positive)' : data?.overall_avg_score < 0 ? 'var(--negative)' : 'var(--neutral)' }}>
            {data?.overall_avg_score != null ? (data.overall_avg_score > 0 ? '+' : '') + data.overall_avg_score.toFixed(4) : '—'}
          </div>
          <div className="stat-meta">по всему корпусу</div>
        </div>
        {items.map(item => (
          <div className="stat-card" key={item.label}>
            <div className="stat-label" style={{ color: COLORS[item.label] }}>{LABELS[item.label] || item.label}</div>
            <div className="stat-value">{item.count}</div>
            <div className="stat-meta">{(item.share * 100).toFixed(1)}% · avg {item.avg_score > 0 ? '+' : ''}{item.avg_score?.toFixed(3)}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Pie chart */}
        <div className="card">
          <div className="card-title">Распределение тональности</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%" cy="45%"
                innerRadius={70} outerRadius={110}
                paddingAngle={3}
                dataKey="value"
              >
                {pieData.map(entry => (
                  <Cell key={entry.label} fill={COLORS[entry.label] || '#64748b'} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value) => <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed breakdown */}
        <div className="card">
          <div className="card-title">Детальная разбивка</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, marginTop: 8 }}>
            {items.map(item => (
              <div key={item.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div>
                    <span className={`badge badge-${item.label}`} style={{ fontSize: 13 }}>
                      {LABELS[item.label] || item.label}
                    </span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: COLORS[item.label], lineHeight: 1 }}>
                      {(item.share * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{item.count} документов</div>
                  </div>
                </div>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${item.share * 100}%`,
                    background: COLORS[item.label],
                    borderRadius: 4,
                    transition: 'width 0.8s ease',
                  }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Средний score</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: COLORS[item.label] }}>
                    {item.avg_score > 0 ? '+' : ''}{item.avg_score?.toFixed(4)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 24, padding: 16,
            background: 'var(--bg-surface)', borderRadius: 8,
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Интерпретация</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {data?.overall_avg_score > 0.05
                ? 'Общий информационный фон корпуса позитивный — преобладают новости о росте, развитии и достижениях.'
                : data?.overall_avg_score < -0.05
                ? 'Общий информационный фон негативный — в повестке доминируют кризисные и конфликтные темы.'
                : 'Информационная повестка сбалансирована — нейтральный тон характерен для аналитических и фактологических материалов.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
