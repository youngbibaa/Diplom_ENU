import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Topics from './pages/Topics'
import Trends from './pages/Trends'
import Sentiment from './pages/Sentiment'
import Documents from './pages/Documents'
import Sources from './pages/Sources'

const PAGE_TITLES = {
  '/': { title: 'Обзор', sub: 'Общая сводка системы анализа трендов' },
  '/topics': { title: 'Темы', sub: 'Тематическое моделирование LDA' },
  '/trends': { title: 'Тренды', sub: 'Динамика упоминаний и trend score' },
  '/sentiment': { title: 'Тональность', sub: 'Анализ sentiment по корпусу' },
  '/documents': { title: 'Документы', sub: 'Все собранные публикации' },
  '/sources': { title: 'Источники', sub: 'RSS-ленты и управление данными' },
}

function PageWrapper() {
  const loc = useLocation()
  const info = PAGE_TITLES[loc.pathname] || { title: 'TrendScope', sub: '' }

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">{info.title}</h1>
        {info.sub && <p className="page-subtitle">{info.sub}</p>}
      </div>
      <div className="page-body">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/topics" element={<Topics />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/sources" element={<Sources />} />
        </Routes>
      </div>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <PageWrapper />
        </main>
      </div>
    </BrowserRouter>
  )
}
