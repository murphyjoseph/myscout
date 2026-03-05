from __future__ import annotations
import logging
from myscout.connectors.base import JobConnector, NormalizedJob

logger = logging.getLogger(__name__)


class UsajobsStubConnector(JobConnector):
    """Stub connector for USAJOBS. Requires API credentials to function."""

    def fetch_jobs(self) -> list[NormalizedJob]:
        logger.warning(
            "USAJOBS connector is a stub. "
            "Set USAJOBS_API_KEY and USAJOBS_EMAIL and implement fetch logic."
        )
        return []
