import sqlite3
from datetime import datetime

UNITS = {"万": 10_000, "w": 10_000, "W": 10_000, "亿": 100_000_000}

def parse_count(v):
    """把 '1.2万' / '10万+' / '3,456' / '赞' 转成整数，转不了返回 None。"""
    # 1. 类型判断放在最前面，避免后面 .strip() 崩掉
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if not isinstance(v, str):
        return None
    # 2. 清洗：空格、千分位逗号、"以上"的加号
    s = v.strip().replace(",", "").replace("+", "").replace(" ", "")
    if not s:
        return None
    # 3. 剥单位：看最后一个字符在不在单位表里
    mult = 1
    if s[-1] in UNITS:
        mult = UNITS[s[-1]]
        s = s[:-1]
    # 4. 剩下的必须能转成数字，否则判定为脏值
    try:
        return int(round(float(s) * mult))
    except ValueError:
        return None


DB = "xhs.db"

UPSERT_SQL = """
INSERT INTO notes (platform, note_id, title, author, author_id,
                   liked, collected, comment, shared, note_url,
                   first_seen_at, last_seen_at, seen_count)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)
ON CONFLICT(platform, note_id) DO UPDATE SET
    title        = excluded.title,
    liked        = excluded.liked,
    collected    = excluded.collected,
    comment      = excluded.comment,
    shared       = excluded.shared,
    last_seen_at = excluded.last_seen_at,
    seen_count   = notes.seen_count + 1
"""


def get_conn(path=DB):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def save_notes(conn, rows, platform="xiaohongshu"):
    """rows 是字典列表。返回 (新增数, 更新数)。"""
    ts = datetime.now().isoformat(timespec="seconds")
    inserted = updated = 0
    for r in rows:
        existed = conn.execute(
            "SELECT 1 FROM notes WHERE platform=? AND note_id=?",
            (platform, r["note_id"]),
        ).fetchone() is not None

        conn.execute(UPSERT_SQL, (
            platform, r["note_id"], r.get("title"), r.get("author"), r.get("author_id"),
            r.get("liked"), r.get("collected"), r.get("comment"), r.get("shared"),
            r.get("note_url"), ts, ts,
        ))
        inserted += 0 if existed else 1
        updated += 1 if existed else 0
    conn.commit()
    return inserted, updated


def stats(conn):
    row = conn.execute(
        "SELECT COUNT(*) AS total, COALESCE(SUM(seen_count), 0) AS seen FROM notes"
    ).fetchone()
    total, seen = row["total"], row["seen"]
    return {
        "唯一笔记": total,
        "累计收到": seen,
        "去重率": round(1 - total / seen, 4) if seen else 0,
    }

if __name__ == "__main__":
    conn = get_conn()
    conn.execute("DELETE FROM notes")

    rows = [
        {"note_id": "n1", "title": "测试1", "liked": parse_count("1.2万"), "author": "小明", "author_id": "u1"},
        {"note_id": "n2", "title": "测试2", "liked": parse_count("赞"), "author": "小红", "author_id": "u2"},
    ]
    print("第 1 次:", save_notes(conn, rows))
    print("第 2 次:", save_notes(conn, rows))
    print(stats(conn))

    for r in conn.execute("SELECT note_id, liked, typeof(liked) AS t, seen_count FROM notes"):
        print(dict(r))
