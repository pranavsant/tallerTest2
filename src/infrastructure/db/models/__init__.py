"""
ORM model registry.

Importing this package registers all SQLAlchemy model classes against
the shared ``Base.metadata``, which is required for Alembic autogenerate
and for ``Base.metadata.create_all`` to work.
"""
from __future__ import annotations

from src.infrastructure.db.models.agent import AgentModel
from src.infrastructure.db.models.alert import AlertModel
from src.infrastructure.db.models.audit_log import AuditLogModel
from src.infrastructure.db.models.call import CallModel
from src.infrastructure.db.models.call_log import CallLogModel
from src.infrastructure.db.models.feed import FeedModel
from src.infrastructure.db.models.incident import IncidentModel
from src.infrastructure.db.models.message import MessageModel
from src.infrastructure.db.models.session import SessionModel
from src.infrastructure.db.models.user import UserModel

__all__ = [
    "AgentModel",
    "AlertModel",
    "AuditLogModel",
    "CallModel",
    "CallLogModel",
    "FeedModel",
    "IncidentModel",
    "MessageModel",
    "SessionModel",
    "UserModel",
]
