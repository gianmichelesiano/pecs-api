"""Add pg_trgm add index 

Revision ID: 4de535e4bc8e
Revises: cfcaa7234fff
Create Date: 2025-03-15 06:31:19.941979

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '4de535e4bc8e'
down_revision = 'cfcaa7234fff'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE INDEX idx_pecs_name_custom_trgm ON pecs USING GIN (name_custom gin_trgm_ops);')
    op.execute('CREATE INDEX idx_pecs_translation_name_trgm ON pecs_translations USING GIN (name gin_trgm_ops);')


def downgrade():
    pass
