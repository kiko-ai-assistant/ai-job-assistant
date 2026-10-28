import logging

import httpx

from config import BackendConfig
from models import Vacancy


class BackendClient:
    def __init__(
        self,
        config: BackendConfig,
        logger: logging.Logger,
    ):
        self.config = config
        self.logger = logger

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def send_vacancies(self, vacancies: list[Vacancy]) -> None:
        if not vacancies:
            self.logger.info("No vacancies to send")
            return

        endpoint = (
            self.config.base_url.rstrip("/")
            + "/"
            + self.config.bulk_path.lstrip("/")
        )

        batch_size = self.config.batch_size

        with httpx.Client(
            timeout=self.config.timeout_seconds,
            headers=self._headers(),
        ) as client:
            for start in range(0, len(vacancies), batch_size):
                batch = vacancies[start:start + batch_size]

                payload = {
                    "vacancies": [
                        vacancy.to_dict()
                        for vacancy in batch
                    ]
                }

                response = client.post(
                    endpoint,
                    json=payload,
                )

                response.raise_for_status()

                self.logger.info(
                    "Sent %s vacancies to backend; HTTP %s",
                    len(batch),
                    response.status_code,
                )
