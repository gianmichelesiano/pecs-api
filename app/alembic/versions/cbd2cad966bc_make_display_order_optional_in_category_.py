"""make display_order optional in Category model

Revision ID: cbd2cad966bc
Revises: da3a23aaf58a
Create Date: 2025-03-06 14:43:12.810171

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'cbd2cad966bc'
down_revision = 'da3a23aaf58a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('categories', 'display_order',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('categories', 'display_order',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
