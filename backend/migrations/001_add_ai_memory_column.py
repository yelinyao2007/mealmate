"""
Migration to add ai_memory column to users table.
This fixes the database schema error that's preventing the app from starting.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add ai_memory column to users table."""
    op.add_column('users', sa.Column('ai_memory', sa.Text(), nullable=True))


def downgrade():
    """Remove ai_memory column from users table."""
    op.drop_column('users', 'ai_memory')