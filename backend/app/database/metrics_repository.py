from app.database.connection import get_connection


class MetricsRepository:

    def ensure_orchestrator_columns(self):
        conn = get_connection()
        cursor = conn.cursor()

        columns = [
            ("orchestrator_intent", "TEXT"),
            ("orchestrator_confidence", "REAL"),
            ("orchestrator_json_valid", "INTEGER"),
            ("orchestrator_schema_valid", "INTEGER"),
            ("orchestrator_tokens", "INTEGER"),
            ("orchestrator_model", "TEXT")
        ]

        for column_name, column_type in columns:
            try:
                cursor.execute(
                    f"ALTER TABLE chat_history ADD COLUMN {column_name} {column_type}"
                )
            except Exception:
                pass

        conn.commit()
        conn.close()

    def save_chat_message(
        self,
        numero: str,
        mensaje: str,
        respuesta: str,
        intent: str,
        latency_seconds: float,
        success: bool = True,
        error: str = None,
        orchestrator: dict = None
    ):
        self.ensure_orchestrator_columns()

        orchestrator = orchestrator or {}

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
                error,
                orchestrator_intent,
                orchestrator_confidence,
                orchestrator_json_valid,
                orchestrator_schema_valid,
                orchestrator_tokens,
                orchestrator_model
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                numero,
                mensaje,
                respuesta,
                intent,
                latency_seconds,
                1 if success else 0,
                error,
                orchestrator.get("intent"),
                orchestrator.get("confidence"),
                1 if orchestrator.get("json_valid") else 0,
                1 if orchestrator.get("schema_valid") else 0,
                orchestrator.get("tokens_used", 0),
                orchestrator.get("model")
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

    def save_intent_test(
        self,
        message: str,
        expected_intent: str,
        detected_intent: str,
        response: str,
        latency_seconds: float
    ):
        expected_clean = (expected_intent or "").strip().lower()
        detected_clean = (detected_intent or "").strip().lower()
        response_clean = (response or "").strip()

        is_correct = expected_clean == detected_clean
        has_response = len(response_clean) > 0

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO intent_tests (
                message,
                expected_intent,
                detected_intent,
                response,
                latency_seconds,
                is_correct,
                has_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message,
                expected_clean,
                detected_clean,
                response,
                latency_seconds,
                1 if is_correct else 0,
                1 if has_response else 0
            )
        )

        conn.commit()
        conn.close()

    def get_chat_history(self, limit: int = 100):
        self.ensure_orchestrator_columns()

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

    def get_intent_tests(self, limit: int = 100):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM intent_tests
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

    def get_inventory_chat_history(self, limit: int = 100):
        self.ensure_orchestrator_columns()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM chat_history
            WHERE intent = 'inventory'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_intent_test_summary(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_tests,
                COALESCE(SUM(is_correct), 0) AS correct_tests,
                COALESCE(AVG(is_correct), 0) AS accuracy,
                COALESCE(AVG(has_response), 0) AS response_rate,
                COALESCE(AVG(latency_seconds), 0) AS avg_latency
            FROM intent_tests
            """
        )

        summary = dict(cursor.fetchone())
        conn.close()

        return summary

    def get_real_chat_analysis(self, limit: int = 100):
        self.ensure_orchestrator_columns()

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

    def get_inventory_summary(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_queries,
                AVG(latency_seconds) AS avg_latency,
                MIN(latency_seconds) AS min_latency,
                MAX(latency_seconds) AS max_latency,
                SUM(success) AS successful_queries,
                AVG(
                    CASE
                        WHEN respuesta IS NOT NULL
                        AND TRIM(respuesta) != ''
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS response_rate,
                AVG(
                    CASE
                        WHEN intent != 'general'
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS intent_precision
            FROM chat_history
            """
        )

        summary = dict(cursor.fetchone())
        conn.close()

        return summary

    def get_quality_metrics(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                expected_intent,
                detected_intent,
                is_correct,
                has_response
            FROM intent_tests
            """
        )

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        total = len(rows)

        if total == 0:
            return {
                "total_tests": 0,
                "accuracy": 0,
                "precision": 0,
                "recall": 0,
                "f1_score": 0,
                "confusion_matrix": {}
            }

        correct = sum(1 for row in rows if row["is_correct"] == 1)

        labels = sorted(
            list(set(
                [row["expected_intent"] for row in rows]
                + [row["detected_intent"] for row in rows]
            ))
        )

        confusion_matrix = {}

        for label in labels:
            confusion_matrix[label] = {}

            for detected in labels:
                confusion_matrix[label][detected] = 0

        for row in rows:
            expected = row["expected_intent"]
            detected = row["detected_intent"]
            confusion_matrix[expected][detected] += 1

        true_positive = correct
        false_positive = total - correct
        false_negative = total - correct

        precision = (
            true_positive / (true_positive + false_positive)
            if (true_positive + false_positive) > 0
            else 0
        )

        recall = (
            true_positive / (true_positive + false_negative)
            if (true_positive + false_negative) > 0
            else 0
        )

        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return {
            "total_tests": total,
            "accuracy": correct / total,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "confusion_matrix": confusion_matrix
        }

    def get_structured_output_metrics(self):
        self.ensure_orchestrator_columns()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_orchestrator_messages,
                AVG(
                    CASE
                        WHEN orchestrator_json_valid = 1
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS json_validity_rate,
                AVG(
                    CASE
                        WHEN orchestrator_schema_valid = 1
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS schema_valid_rate
            FROM chat_history
            WHERE orchestrator_model IS NOT NULL
            AND TRIM(orchestrator_model) != ''
            """
        )

        summary = dict(cursor.fetchone())
        conn.close()

        return {
            "total_messages": summary["total_orchestrator_messages"] or 0,
            "json_validity_rate": summary["json_validity_rate"] or 0,
            "schema_valid_rate": summary["schema_valid_rate"] or 0
        }

    def get_architecture_metrics(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                AVG(success) AS architecture_success_rate
            FROM chat_history
            """
        )

        summary = dict(cursor.fetchone())
        conn.close()

        return {
            "total_requests": summary["total_requests"] or 0,
            "architecture_success_rate": summary["architecture_success_rate"] or 0
        }

    def get_operation_metrics(self):
        self.ensure_orchestrator_columns()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_messages,
                AVG(latency_seconds) AS avg_latency,
                MIN(latency_seconds) AS min_latency,
                MAX(latency_seconds) AS max_latency
            FROM chat_history
            """
        )

        chat = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT
                SUM(prompt_tokens) AS prompt_tokens,
                SUM(completion_tokens) AS completion_tokens,
                SUM(total_tokens) AS total_tokens,
                AVG(tokens_per_second) AS avg_tokens_per_second,
                AVG(latency_seconds) AS avg_llm_latency
            FROM llm_metrics
            """
        )

        llm = dict(cursor.fetchone())

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_orchestrator_calls,
                SUM(orchestrator_tokens) AS orchestrator_tokens,
                AVG(orchestrator_confidence) AS avg_orchestrator_confidence,
                AVG(
                    CASE
                        WHEN orchestrator_json_valid = 1
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS orchestrator_json_valid_rate,
                AVG(
                    CASE
                        WHEN orchestrator_schema_valid = 1
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS orchestrator_schema_valid_rate
            FROM chat_history
            WHERE orchestrator_model IS NOT NULL
            AND TRIM(orchestrator_model) != ''
            """
        )

        orchestrator = dict(cursor.fetchone())

        conn.close()

        return {
            "chat": {
                "total_messages": chat["total_messages"] or 0,
                "avg_latency": chat["avg_latency"] or 0,
                "min_latency": chat["min_latency"] or 0,
                "max_latency": chat["max_latency"] or 0
            },
            "llm": {
                "prompt_tokens": llm["prompt_tokens"] or 0,
                "completion_tokens": llm["completion_tokens"] or 0,
                "total_tokens": llm["total_tokens"] or 0,
                "avg_tokens_per_second": llm["avg_tokens_per_second"] or 0,
                "avg_llm_latency": llm["avg_llm_latency"] or 0
            },
            "orchestrator": {
                "total_calls": orchestrator["total_orchestrator_calls"] or 0,
                "total_tokens": orchestrator["orchestrator_tokens"] or 0,
                "avg_confidence": orchestrator["avg_orchestrator_confidence"] or 0,
                "json_valid_rate": orchestrator["orchestrator_json_valid_rate"] or 0,
                "schema_valid_rate": orchestrator["orchestrator_schema_valid_rate"] or 0
            }
        }