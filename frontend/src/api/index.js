const BASE = '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

async function post(path, body = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  // Dashboard
  getDashboardSummary: () => get('/dashboard/summary'),

  // Analytics
  getTopics: () => get('/analytics/topics'),
  getSentimentSummary: () => get('/analytics/sentiment-summary'),
  getTopicTimeline: (topicId) => get(`/analytics/topics/${topicId}/timeline`),
  getTopicDocuments: (topicId, limit = 10, offset = 0) =>
    get(`/analytics/topics/${topicId}/documents?limit=${limit}&offset=${offset}`),
  getRuns: () => get('/analytics/runs'),
  runAnalytics: () => post('/analytics/run'),

  // Trends
  getTopTrends: () => get('/trends/top'),
  getAllTrends: () => get('/trends'),
  getTrendTimeline: () => get('/trends/timeline'),

  // Documents
  getDocuments: (params = {}) => {
    const q = new URLSearchParams()
    if (params.limit) q.set('limit', params.limit)
    if (params.offset) q.set('offset', params.offset)
    if (params.topic_id) q.set('topic_id', params.topic_id)
    if (params.sentiment_label) q.set('sentiment_label', params.sentiment_label)
    return get(`/documents?${q.toString()}`)
  },

  // Sources
  getSources: () => get('/sources'),
  getApprovedSources: () => get('/sources/approved'),
  ingestBulk: (urls) => post('/ingestion/rss/bulk', { feed_urls: urls }),
  cleanupRussian: () => post('/sources/cleanup'),
}
