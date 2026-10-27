"""Add validation constraints to attrition history.

Revision ID: 20261026_0002
Revises: 20261025_0001
"""

from alembic import op


revision = "20261026_0002"
down_revision = "20261025_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Prevent invalid attrition prediction values."""
    with op.batch_alter_table("attrition_history") as batch_op:
        batch_op.create_check_constraint(
            "ck_attrition_history_probability_range",
            "attrition_probability >= 0 AND attrition_probability <= 1",
        )
        batch_op.create_check_constraint(
            "ck_attrition_history_risk_percentage_range",
            "attrition_risk_percentage >= 0 AND attrition_risk_percentage <= 100",
        )
        batch_op.create_check_constraint(
            "ck_attrition_history_risk_level",
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH')",
        )


def downgrade() -> None:
    """Remove only the constraints introduced by this revision."""
    with op.batch_alter_table("attrition_history") as batch_op:
        batch_op.drop_constraint(
            "ck_attrition_history_risk_level",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_attrition_history_risk_percentage_range",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_attrition_history_probability_range",
            type_="check",
        )
