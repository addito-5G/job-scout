"""Контекстный менеджер для SQLAlchemy-сессий (без изменения commit-семантики)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from db.engine import get_session, init_db


@contextmanager
def session_scope(*, init: bool = True) -> Iterator[Session]:
    """
  Открыть сессию и гарантированно закрыть её.

  Не делает auto-commit: вызывающий код сам вызывает session.commit(),
  как и при ручном get_session().
  """
    if init:
        init_db()
    session = get_session()
    try:
        yield session
    finally:
        session.close()
