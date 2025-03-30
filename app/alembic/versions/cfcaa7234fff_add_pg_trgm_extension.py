"""Add pg_trgm extension

Revision ID: cfcaa7234fff
Revises: 752dc737c08d
Create Date: 2025-03-15 06:02:35.085455

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'cfcaa7234fff'
down_revision = '752dc737c08d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

def downgrade():
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
