"""Add nome table

Revision ID: 846b7c19009b
Revises: a9e643253934
Create Date: 2025-03-01 16:48:30.266287

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '846b7c19009b'
down_revision = 'a9e643253934'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('nome',
    sa.Column('pictogram_id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('lang', sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pictogram_id'], ['pictogram.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nome_lang'), 'nome', ['lang'], unique=False)
    op.create_index(op.f('ix_nome_name'), 'nome', ['name'], unique=False)
    op.create_index(op.f('ix_nome_pictogram_id'), 'nome', ['pictogram_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_nome_pictogram_id'), table_name='nome')
    op.drop_index(op.f('ix_nome_name'), table_name='nome')
    op.drop_index(op.f('ix_nome_lang'), table_name='nome')
    op.drop_table('nome')
    # ### end Alembic commands ###
