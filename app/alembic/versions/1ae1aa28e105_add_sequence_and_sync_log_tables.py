"""add_sequence_and_sync_log_tables

Revision ID: 1ae1aa28e105
Revises: 2f6ddeae325e
Create Date: 2025-03-06 12:16:42.518661

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1ae1aa28e105'
down_revision = '2f6ddeae325e'
branch_labels = None
depends_on = None


def upgrade():
    # Crea la tabella categories
    op.create_table('categories',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('color', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_custom', sa.Boolean(), nullable=False),
        sa.Column('is_visible', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Elimina la tabella categories
    op.drop_table('categories')
