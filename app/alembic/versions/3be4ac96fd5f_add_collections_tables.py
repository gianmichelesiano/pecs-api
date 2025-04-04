"""add_collections_tables

Revision ID: 3be4ac96fd5f
Revises: 4de535e4bc8e
Create Date: 2025-03-15 10:14:14.579391

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '3be4ac96fd5f'
down_revision = '4de535e4bc8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('collections',
    sa.Column('is_custom', sa.Boolean(), nullable=False),
    sa.Column('is_visible', sa.Boolean(), nullable=False),
    sa.Column('name_custom', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('icon', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('color', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('collections_translations',
    sa.Column('language_code', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('collection_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('phrase_collections',
    sa.Column('phrase_id', sa.Uuid(), nullable=False),
    sa.Column('collection_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
    sa.ForeignKeyConstraint(['phrase_id'], ['phrases.id'], ),
    sa.PrimaryKeyConstraint('phrase_id', 'collection_id')
    )
    op.drop_index('idx_pecs_name_custom_trgm', table_name='pecs', postgresql_using='gin')
    op.drop_index('idx_pecs_translation_name_trgm', table_name='pecs_translations', postgresql_using='gin')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_pecs_translation_name_trgm', 'pecs_translations', ['name'], unique=False, postgresql_using='gin')
    op.create_index('idx_pecs_name_custom_trgm', 'pecs', ['name_custom'], unique=False, postgresql_using='gin')
    op.drop_table('phrase_collections')
    op.drop_table('collections_translations')
    op.drop_table('collections')
    # ### end Alembic commands ###
