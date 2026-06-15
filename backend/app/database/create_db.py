from app.database.connection import get_connection


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            quantity INTEGER NOT NULL,
            source TEXT,
            last_update DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            usuario_id INTEGER PRIMARY KEY AUTOINCREMENT,
            whatsapp_number TEXT UNIQUE,
            nombre TEXT,
            edad INTEGER,
            sexo TEXT,
            peso REAL,
            altura REAL,
            activity_level TEXT,
            objetivo TEXT,
            dietary_restrictions TEXT,
            food_preferences TEXT,
            budget REAL,
            ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Database created")
