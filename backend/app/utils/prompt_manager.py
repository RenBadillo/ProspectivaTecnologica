from pathlib import Path


class PromptManager:

    BASE_PATH = (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "prompts"
    )

    @classmethod
    def load(
        cls,
        filename: str
    ) -> str:

        path = cls.BASE_PATH / filename

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()