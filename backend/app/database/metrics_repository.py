from app.database.connection import get_connection


class MetricsRepository:

    def save_chat_message(
        self,
        numero: str,
        mensaje: str,
        respuesta: str,
        intent: str,
        latency_seconds: float,
        success: bool = True,
        error: str = None
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_history (
                numero,
                mensaje,
                respuesta,
                intent,
                latency_seconds,
                success,
                error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                numero,
                mensaje,
                respuesta,
                intent,
                latency_seconds,
                1 if success else 0,
                error
            )
        )

        conn.commit()
        conn.close()

    def save_llm_metric(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_seconds: float,
        tokens_per_second: float
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO llm_metrics (
                model,
                provider,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                latency_seconds,
                tokens_per_second
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model,
                provider,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                latency_seconds,
                tokens_per_second
            )
        )

        conn.commit()
        conn.close()

    def get_chat_history(self, limit: int = 100):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM chat_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_llm_metrics(self, limit: int = 100):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM llm_metrics
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_summary(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_messages,
                AVG(latency_seconds) AS avg_latency
            FROM chat_history
            """
        )

        chat_summary = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_llm_calls,
                SUM(prompt_tokens) AS prompt_tokens,
                SUM(completion_tokens) AS completion_tokens,
                SUM(total_tokens) AS total_tokens,
                AVG(latency_seconds) AS avg_llm_latency,
                AVG(tokens_per_second) AS avg_tokens_per_second
            FROM llm_metrics
            """
        )

        llm_summary = dict(cursor.fetchone())

        conn.close()

        return {
            "chat": chat_summary,
            "llm": llm_summary
        }