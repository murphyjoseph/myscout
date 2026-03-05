from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NormalizedJob:
    source: str
    external_id: str
    url: str
    company: str
    title: str
    location: str | None = None
    remote_type: str | None = None
    employment_type: str | None = None
    description: str | None = None
    date_posted: datetime | None = None
    comp_min: float | None = None
    comp_max: float | None = None
    comp_currency: str | None = None


class JobConnector:
    """Base class for all job connectors."""

    def __init__(self, company: str, conn_cfg: dict[str, Any], source_cfg: dict[str, Any]):
        self.company = company
        self.conn_cfg = conn_cfg
        self.source_cfg = source_cfg

    def fetch_jobs(self) -> list[NormalizedJob]:
        raise NotImplementedError
