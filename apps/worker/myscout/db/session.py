from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

_engine = None


def get_engine():
    # LOCAL-ONLY: Hardcoded default credentials. In a real service you'd
    # require DATABASE_URL from the environment and never ship defaults.
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL", "postgresql://myscout:myscout@localhost:5432/myscout")
        _engine = create_engine(url, echo=False)
    return _engine


def get_session() -> Session:
    engine = get_engine()
    return sessionmaker(bind=engine)()
