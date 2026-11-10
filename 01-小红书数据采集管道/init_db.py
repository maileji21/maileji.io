import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS notes (
    platform      TEXT NOT NULL,
    note_id       TEXT NOT NULL,
    title         TEXT,
    author        TEXT,
    author_id     TEXT,
    note_url      TEXT,
    xsec_token    TEXT,
    liked         INTEGER,
    collected     INTEGER,
    comment       INTEGER,
    shared        INTEGER,
    first_seen_at TEXT,
    last_seen_at  TEXT,
    seen_count    INTEGER DEFAULT 1,
    has_time      INTEGER DEFAULT 0,
    raw           TEXT,
    PRIMARY KEY (platform, note_id)
);

CREATE TABLE IF NOT EXISTS crawl_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    keyword  TEXT NOT NULL,
    page_no  INTEGER NOT NULL,
    raw      INTEGER,
    new_cnt  INTEGER,
    dup_cnt  INTEGER,
    skipped  INTEGER,
    cost_s   REAL,
    ts       TEXT
);
"""

conn = sqlite3.connect("xhs.db")
conn.executescript(DDL)      # 执行上面那段 SQL 文本
conn.commit()

print("表:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("字段数:", conn.execute("SELECT count(*) FROM pragma_table_info('notes')").fetchone()[0])
conn.close()
