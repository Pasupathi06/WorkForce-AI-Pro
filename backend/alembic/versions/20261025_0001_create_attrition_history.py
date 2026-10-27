"""Create attrition history table.

Revision ID: 20261025_0001
Revises: 20261025_0000
"""

from alembic import op
import sqlalchemy as sa


revision = "20261025_0001"
down_revision = "20261025_0000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create attrition history without recreating existing tables."""
    op.create_table(
        "attrition_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("predicted_by_user_id", sa.Integer(), nullable=False),
        sa.Column("attrition_probability", sa.Float(), nullable=False),
        sa.Column("attrition_risk_percentage", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=10), nullable=False),
        sa.Column("model_type", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["predicted_by_user_id"],
            ["users.id"],
        ),
    )

    op.create_index(
        "ix_attrition_history_id",
        "attrition_history",
        ["id"],
    )
    op.create_index(
        "ix_attrition_history_employee_id",
        "attrition_history",
        ["employee_id"],
    )
    op.create_index(
        "ix_attrition_history_predicted_by_user_id",
        "attrition_history",
        ["predicted_by_user_id"],
    )
    op.create_index(
        "ix_attrition_history_risk_level",
        "attrition_history",
        ["risk_level"],
    )
    op.create_index(
        "ix_attrition_history_created_at",
        "attrition_history",
        ["created_at"],
    )


def downgrade() -> None:
    """Remove only the attrition history table."""
    op.drop_index(
        "ix_attrition_history_created_at",
        table_name="attrition_history",
    )
    op.drop_index(
        "ix_attrition_history_risk_level",
        table_name="attrition_history",
    )
    op.drop_index(
        "ix_attrition_history_predicted_by_user_id",
        table_name="attrition_history",
    )
    op.drop_index(
        "ix_attrition_history_employee_id",
        table_name="attrition_history",
    )
    op.drop_index(
        "ix_attrition_history_id",
        table_name="attrition_history",
    )
    op.drop_table("attrition_history")
