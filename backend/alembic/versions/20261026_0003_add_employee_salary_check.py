from alembic import op

revision = "20261026_0003"
down_revision = "20261026_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE employees "
        "ADD CONSTRAINT ck_employees_salary_non_negative "
        "CHECK (salary >= 0)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE employees "
        "DROP CHECK ck_employees_salary_non_negative"
    )
