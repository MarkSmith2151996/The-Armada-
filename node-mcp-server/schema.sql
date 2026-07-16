CREATE TABLE IF NOT EXISTS worker_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    ai_id TEXT NOT NULL,
    node TEXT NOT NULL,
    started_at DATETIME DEFAULT (datetime('now')),
    ended_at DATETIME,
    turn_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS tool_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES worker_sessions(session_id),
    turn INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    query TEXT,
    result_summary TEXT NOT NULL,
    full_result TEXT NOT NULL,
    token_estimate INTEGER,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS tool_results_fts USING fts5(
    query, result_summary, full_result,
    content='tool_results',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS tool_results_ai AFTER INSERT ON tool_results BEGIN
    INSERT INTO tool_results_fts(rowid, query, result_summary, full_result)
    VALUES (new.id, new.query, new.result_summary, new.full_result);
END;

CREATE TABLE IF NOT EXISTS session_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES worker_sessions(session_id),
    tool_calls_count INTEGER,
    searches_count INTEGER,
    pages_browsed INTEGER,
    total_input_tokens_estimate INTEGER,
    total_output_tokens_estimate INTEGER,
    duration_seconds REAL,
    created_at DATETIME DEFAULT (datetime('now'))
);
