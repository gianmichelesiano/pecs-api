"""add_sequence_pictogram_positions_table

Revision ID: 9e7bb07f125d
Revises: add_cascade_pictogram_rel
Create Date: 2025-03-07 17:20:44.337001

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9e7bb07f125d'
down_revision = 'add_cascade_pictogram_rel'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sequence_pictogram_positions',
    sa.Column('sequence_id', sa.Uuid(), nullable=False),
    sa.Column('pictogram_id', sa.Uuid(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pictogram_id'], ['pictograms.id'], ),
    sa.ForeignKeyConstraint(['sequence_id'], ['sequences.id'], ),
    sa.PrimaryKeyConstraint('sequence_id', 'pictogram_id')
    )
    op.drop_table('sequence_items')
    op.drop_constraint('pictogram_categories_pictogram_id_fkey', 'pictogram_categories', type_='foreignkey')
    op.create_foreign_key(None, 'pictogram_categories', 'pictograms', ['pictogram_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pictogram_categories', type_='foreignkey')
    op.create_foreign_key('pictogram_categories_pictogram_id_fkey', 'pictogram_categories', 'pictograms', ['pictogram_id'], ['id'], ondelete='CASCADE')
    op.create_table('sequence_items',
    sa.Column('sequence_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('pictogram_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('position', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['pictogram_id'], ['pictograms.id'], name='sequence_items_pictogram_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sequence_id'], ['sequences.id'], name='sequence_items_sequence_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='sequence_items_pkey')
    )
    op.drop_table('sequence_pictogram_positions')
    # ### end Alembic commands ###
