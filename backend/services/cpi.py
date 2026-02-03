import json
from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple

import httpx

from backend.config import get_calculation_config
from backend.config import Settings


@dataclass
class CPIInfo:
    """CPI value for a specific month/year and derived index factor."""

    year: int
    month: int
    cpi_index: float

    @property
    def index_factor(self) -> float:
        return self.cpi_index / get_calculation_config().cpi_base_oct_2001


class CPIDataError(RuntimeError):
    """Raised when CPI data cannot be fetched or parsed."""


class CPIFetcherService:
    """Fetches Consumer Price Index from GENESIS API"""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: Dict[Tuple[int, int], CPIInfo] = {}

    def _table_headers(self) -> dict:
        if not self._settings.genesis_username or not self._settings.genesis_password:
            raise CPIDataError(
                "GENESIS credentials required: set GENESIS_USERNAME and GENESIS_PASSWORD"
            )
        return {
            "accept": "application/json; charset=UTF-8",
            "username": self._settings.genesis_username,
            "password": self._settings.genesis_password,
        }

    def _table_form_data(self, target_year: int) -> dict:
        """Form body for GENESIS API."""
        year_str = str(target_year)
        return {
            "regionalkey": "",
            "compress": "false",
            "name": self._settings.genesis_cpi_code,
            "area": "free",
            "timeslices": "",
            "classifyingkey1": "",
            "classifyingkey2": "",
            "classifyingkey3": "",
            "classifyingkey4": "",
            "classifyingkey5": "",
            "stand": "01.01.1970 01:00",
            "classifyingvariable1": "",
            "classifyingvariable2": "",
            "language": self._settings.genesis_language,
            "endyear": year_str,
            "classifyingvariable3": "",
            "transpose": "false",
            "classifyingvariable4": "",
            "contents": "",
            "classifyingvariable5": "",
            "regionalvariable": "",
            "job": "false",
            "startyear": year_str,
        }

    def _fetch_table_json(self, target_year: int) -> dict:
        """POST /data/table and return JSON."""
        url = f"{self._settings.genesis_base_url}/data/table"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    url,
                    headers=self._table_headers(),
                    data=self._table_form_data(target_year),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise CPIDataError(f"GENESIS table request failed: {exc.response.text}") from exc
        except json.JSONDecodeError as exc:
            raise CPIDataError(f"GENESIS table returned invalid JSON: {exc}") from exc
        except Exception as exc:
            raise CPIDataError(f"GENESIS table request failed: {exc}") from exc

    def _parse_cpi_from_content(self, content: str, target_year: int) -> CPIInfo:
        """
        Search the csv file for the CPI value for the target year
        """
        target_year_str = str(target_year)
        october_names = ("october", "oktober")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "__________":
                break
            if not stripped:
                continue
            cells = [c.strip() for c in line.split(";")]
            if len(cells) < 3:
                continue
            if cells[0] != target_year_str:
                continue
            month_cell = cells[1].lower()
            if month_cell not in october_names:
                continue
            try:
                cpi_value = float(cells[2].replace(",", "."))
            except ValueError:
                continue
            if 0 < cpi_value <= 1000:
                return CPIInfo(year=target_year, month=10, cpi_index=cpi_value)
        raise CPIDataError(f"No CPI row found for October {target_year} in CPI table")

    async def get_cpi_for_prev_year(self, purchase_date: date) -> CPIInfo:
        """Return CPI for October of the year prior."""
        target_year = purchase_date.year - 1
        cache_key = (target_year, 10)
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = await self._fetch_table_async(target_year)
        status = data.get("Status") or {}
        if status.get("Code") != 0:
            raise CPIDataError(
                f"GENESIS table error: {status.get('Content', 'unknown')}"
            )
        obj = data.get("Object") or {}
        content = obj.get("Content")
        if not content:
            raise CPIDataError("GENESIS table response has no Object.Content")

        info = self._parse_cpi_from_content(content, target_year)
        self._cache[cache_key] = info
        return info

    async def _fetch_table_async(self, target_year: int) -> dict:
        """Fetch CPI table for the given year return JSON."""
        url = f"{self._settings.genesis_base_url}/data/table"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    headers=self._table_headers(),
                    data=self._table_form_data(target_year),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            raise CPIDataError(f"GENESIS table request failed: {exc.response.text}") from exc
        except json.JSONDecodeError as exc:
            raise CPIDataError(f"GENESIS table returned invalid JSON: {exc}") from exc
        except Exception as exc:
            raise CPIDataError(f"GENESIS table request failed: {exc}") from exc
