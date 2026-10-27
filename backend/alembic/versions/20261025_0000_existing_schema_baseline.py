"""Baseline for existing workforce_ai_pro tables.

This revision records the existing schema as a baseline.
It intentionally does not create or alter existing tables.

Revision ID: 20261025_0000
Revises:
"""

from alembic import op

revision = "20261025_0000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Existing users, departments, and employees tables are preserved."""
    pass


def downgrade() -> None:
    """Baseline downgrade intentionally leaves existing tables untouched."""
    pass
