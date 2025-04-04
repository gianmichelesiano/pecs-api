"""add origin field to phrase

Revision ID: afa4ff3971fb
Revises: 3be4ac96fd5f
Create Date: 2025-03-31 21:23:45.480147

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'afa4ff3971fb'
down_revision = '3be4ac96fd5f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if table exists before trying to drop its indexes and the table itself
    if 'langchain_pg_embedding' in inspector.get_table_names():
        # Check if indexes exist before dropping them
        indexes = inspector.get_indexes('langchain_pg_embedding')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_cmetadata_gin' in index_names:
            op.drop_index('ix_cmetadata_gin', table_name='langchain_pg_embedding', postgresql_using='gin')
        if 'ix_langchain_pg_embedding_id' in index_names:
            op.drop_index('ix_langchain_pg_embedding_id', table_name='langchain_pg_embedding')
        
        op.drop_table('langchain_pg_embedding')
    
    if 'langchain_pg_collection' in inspector.get_table_names():
        op.drop_table('langchain_pg_collection')
    
    op.add_column('phrases', sa.Column('origin', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('phrases', 'origin')
    op.create_table('langchain_pg_collection',
    sa.Column('uuid', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('cmetadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
    sa.UniqueConstraint('name', name='langchain_pg_collection_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('langchain_pg_embedding',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('collection_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('embedding', sa.NullType(), autoincrement=False, nullable=True),
    sa.Column('document', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], name='langchain_pg_embedding_collection_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='langchain_pg_embedding_pkey')
    )
    op.create_index('ix_langchain_pg_embedding_id', 'langchain_pg_embedding', ['id'], unique=True)
    op.create_index('ix_cmetadata_gin', 'langchain_pg_embedding', ['cmetadata'], unique=False, postgresql_using='gin')
    # ### end Alembic commands ###
