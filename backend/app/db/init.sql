CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    text_raw TEXT NOT NULL,
    text_clean TEXT,
    url TEXT,
    author VARCHAR(255),
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sentiment_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    label VARCHAR(20) NOT NULL,
    score DOUBLE PRECISION NOT NULL
);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    keywords TEXT NOT NULL
);

CREATE TABLE document_topics (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    probability DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

CREATE TABLE trend_metrics (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mentions_count INTEGER NOT NULL DEFAULT 0,
    growth_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    sentiment_avg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    trend_score DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

CREATE INDEX idx_documents_source_id ON documents(source_id);
CREATE INDEX idx_documents_published_at ON documents(published_at);
CREATE INDEX idx_documents_collected_at ON documents(collected_at);
CREATE INDEX idx_documents_url ON documents(url);

CREATE INDEX idx_sentiment_results_document_id ON sentiment_results(document_id);

CREATE INDEX idx_document_topics_document_id ON document_topics(document_id);
CREATE INDEX idx_document_topics_topic_id ON document_topics(topic_id);

CREATE INDEX idx_trend_metrics_topic_id ON trend_metrics(topic_id);
CREATE INDEX idx_trend_metrics_date ON trend_metrics(date);
CREATE INDEX idx_trend_metrics_topic_date ON trend_metrics(topic_id, date);