"""recreate_after_alembic_version_deletion

Revision ID: 2f6ddeae325e
Revises: 45a76dcabd8a
Create Date: 2025-03-06 12:14:20.998132

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '2f6ddeae325e'
down_revision = '45a76dcabd8a'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
