"""Create the research intelligence schema.

Revision ID: 20261119_001
Revises:
"""
from alembic import op
from app.database.session import Base
import app.models.entities  # noqa: F401 - registers all metadata

revision = "20261119_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
