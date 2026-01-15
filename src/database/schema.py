"""Schema SQL do MariaBicoBot."""
import sqlite3

# SQL para criar as tabelas
SQL_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_PRODUCTS_SEEN = """
CREATE TABLE IF NOT EXISTS products_seen (
    item_id INTEGER PRIMARY KEY,
    first_seen_at DATETIME NOT NULL,
    last_seen_at DATETIME NOT NULL,
    last_price_min REAL,
    last_discount_rate INTEGER,
    last_commission REAL,
    last_commission_rate REAL,
    last_score REAL,
    raw_json TEXT
);
"""

SQL_CREATE_PRODUCTS_SEEN_INDEX = """
CREATE INDEX IF NOT EXISTS idx_products_seen_last_seen
ON products_seen(last_seen_at);
"""

SQL_CREATE_LINKS = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_url TEXT UNIQUE NOT NULL,
    short_link TEXT NOT NULL,
    sub_ids_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME
);
"""

SQL_CREATE_LINKS_INDEXES = [
    """
CREATE INDEX IF NOT EXISTS idx_links_origin
ON links(origin_url);
""",
    """
CREATE INDEX IF NOT EXISTS idx_links_created
ON links(created_at);
""",
]

SQL_CREATE_SENT_MESSAGES = """
CREATE TABLE IF NOT EXISTS sent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    group_id TEXT NOT NULL,
    short_link TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    batch_id TEXT,
    FOREIGN KEY (item_id) REFERENCES products_seen(item_id)
);
"""

SQL_CREATE_SENT_MESSAGES_INDEXES = [
    """
CREATE INDEX IF NOT EXISTS idx_sent_item_group
ON sent_messages(item_id, group_id);
""",
    """
CREATE INDEX IF NOT EXISTS idx_sent_batch
ON sent_messages(batch_id);
""",
]

SQL_CREATE_RUNS = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,
    started_at DATETIME NOT NULL,
    ended_at DATETIME,
    items_fetched INTEGER DEFAULT 0,
    items_approved INTEGER DEFAULT 0,
    items_sent INTEGER DEFAULT 0,
    error_summary TEXT,
    success BOOLEAN DEFAULT 1
);
"""

SQL_CREATE_RUNS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_runs_started
ON runs(started_at DESC);
"""

# Todas as queries de criação
ALL_CREATE_STATEMENTS = [
    SQL_CREATE_SETTINGS,
    SQL_CREATE_PRODUCTS_SEEN,
    SQL_CREATE_PRODUCTS_SEEN_INDEX,
    SQL_CREATE_LINKS,
    *SQL_CREATE_LINKS_INDEXES,
    SQL_CREATE_SENT_MESSAGES,
    *SQL_CREATE_SENT_MESSAGES_INDEXES,
    SQL_CREATE_RUNS,
    SQL_CREATE_RUNS_INDEX,
]


def init_db(db_path: str) -> sqlite3.Connection:
    """Inicializa o banco de dados criando todas as tabelas.

    Args:
        db_path: Caminho para o arquivo SQLite

    Returns:
        Conexão com o banco de dados
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Habilita foreign keys (SQLite precisa ser habilitado por conexão)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()
    for statement in ALL_CREATE_STATEMENTS:
        cursor.execute(statement)

    conn.commit()
    return conn


def get_connection(db_path: str) -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados.

    Args:
        db_path: Caminho para o arquivo SQLite

    Returns:
        Conexão com o banco de dados
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Habilita foreign keys (SQLite precisa ser habilitado por conexão)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# SQL para queries comuns
SQL_SELECT_SETTINGS_BY_KEY = """
SELECT value FROM settings WHERE key = ?;
"""

SQL_UPSERT_SETTING = """
INSERT OR REPLACE INTO settings (key, value, updated_at)
VALUES (?, ?, CURRENT_TIMESTAMP);
"""

SQL_SELECT_PRODUCT_SEEN = """
SELECT * FROM products_seen WHERE item_id = ?;
"""

SQL_UPSERT_PRODUCT_SEEN = """
INSERT INTO products_seen (
    item_id, first_seen_at, last_seen_at,
    last_price_min, last_discount_rate,
    last_commission, last_commission_rate,
    last_score, raw_json
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(item_id) DO UPDATE SET
    last_seen_at = excluded.last_seen_at,
    last_price_min = excluded.last_price_min,
    last_discount_rate = excluded.last_discount_rate,
    last_commission = excluded.last_commission,
    last_commission_rate = excluded.last_commission_rate,
    last_score = excluded.last_score,
    raw_json = excluded.raw_json;
"""

SQL_SELECT_LINK_BY_ORIGIN = """
SELECT * FROM links
WHERE origin_url = ?
AND created_at > datetime('now', '-30 days');
"""

SQL_INSERT_LINK = """
INSERT INTO links (origin_url, short_link, sub_ids_json, created_at)
VALUES (?, ?, ?, CURRENT_TIMESTAMP)
RETURNING id, origin_url, short_link, sub_ids_json, created_at;
"""

SQL_UPDATE_LINK_LAST_USED = """
UPDATE links SET last_used_at = CURRENT_TIMESTAMP
WHERE id = ?;
"""

SQL_SELECT_SENT_RECENT = """
SELECT COUNT(*) as count FROM sent_messages
WHERE item_id = ?
AND group_id = ?
AND sent_at > datetime('now', '-{days} days');
"""

SQL_INSERT_SENT_MESSAGE = """
INSERT INTO sent_messages (item_id, group_id, short_link, sent_at, batch_id)
VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?);
"""

SQL_INSERT_RUN_START = """
INSERT INTO runs (run_type, started_at)
VALUES (?, CURRENT_TIMESTAMP)
RETURNING id;
"""

SQL_UPDATE_RUN_END = """
UPDATE runs SET
    ended_at = CURRENT_TIMESTAMP,
    items_fetched = ?,
    items_approved = ?,
    items_sent = ?,
    error_summary = ?,
    success = ?
WHERE id = ?;
"""

SQL_SELECT_LAST_RUN = """
SELECT * FROM runs
ORDER BY started_at DESC
LIMIT 1;
"""

SQL_SELECT_RUNS_STATS = """
SELECT
    COUNT(*) as total_runs,
    SUM(items_fetched) as total_fetched,
    SUM(items_approved) as total_approved,
    SUM(items_sent) as total_sent
FROM runs;
"""

SQL_SELECT_DB_STATS = """
SELECT
    (SELECT COUNT(*) FROM products_seen) as unique_products,
    (SELECT COUNT(*) FROM links) as total_links,
    (SELECT COUNT(*) FROM sent_messages) as total_sent;
"""

SQL_VACUUM = "VACUUM;"
