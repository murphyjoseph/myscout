from __future__ import annotations
import logging
from typing import Any
from myscout.connectors.base import JobConnector
from myscout.connectors.lever import LeverConnector
from myscout.connectors.greenhouse import GreenhouseConnector
from myscout.connectors.ashby import AshbyConnector
from myscout.connectors.remotive import RemotiveConnector
from myscout.connectors.adzuna import AdzunaConnector
from myscout.connectors.usajobs_stub import UsajobsStubConnector
from myscout.connectors.site import SiteConnector
from myscout.connectors.browser import BrowserConnector

logger = logging.getLogger(__name__)

_CONNECTOR_MAP: dict[str, type[JobConnector]] = {
    "lever": LeverConnector,
    "greenhouse": GreenhouseConnector,
    "ashby": AshbyConnector,
    "remotive": RemotiveConnector,
    "adzuna": AdzunaConnector,
    "usajobs": UsajobsStubConnector,
    "site": SiteConnector,
    "browser": BrowserConnector,
}


def get_connector(
    conn_type: str,
    company: str,
    conn_cfg: dict[str, Any],
    source_cfg: dict[str, Any],
) -> JobConnector | None:
    cls = _CONNECTOR_MAP.get(conn_type)
    if cls is None:
        return None
    return cls(company=company, conn_cfg=conn_cfg, source_cfg=source_cfg)
