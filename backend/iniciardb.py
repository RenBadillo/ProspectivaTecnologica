import sqlite3

conn = sqlite3.connect("app/database/inventory.db")
cur = conn.cursor()


cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())

# cur.execute("""

#     CREATE TABLE IF NOT EXISTS chat_history (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         numero TEXT,
#         mensaje TEXT,
#         respuesta TEXT,
#         intent TEXT,
#         latency_seconds REAL,
#         success INTEGER DEFAULT 1,
#         error TEXT,
#         created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
#         orchestrator_intent TEXT, 
#         orchestrator_confidence REAL, 
#         orchestrator_json_valid INTEGER, 
#         orchestrator_schema_valid INTEGER, 
#         orchestrator_tokens INTEGER, 
#         orchestrator_model TEXT
#     )

#     """)


# cur.execute("""

#     CREATE TABLE IF NOT EXISTS llm_metrics (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         model TEXT,
#         provider TEXT,
#         prompt_tokens INTEGER DEFAULT 0,
#         completion_tokens INTEGER DEFAULT 0,
#         total_tokens INTEGER DEFAULT 0,
#         latency_seconds REAL DEFAULT 0,
#         tokens_per_second REAL DEFAULT 0,
#         created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#     )

#             """)


conn.commit()
conn.close()


