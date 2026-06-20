"""
Migration to add source_user_id column to notifications table.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add source_user_id column to notifications table."""
    op.add_column('notifications', sa.Column('source_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_notifications_source_user_id', 'notifications', 'users', ['source_user_id', 'id'])


def downgrade():
    """Remove source_user_id column from notifications table."""
    op.drop_constraint('fk_notifications_source_user_id', 'notifications')
    op.drop_column('notifications', 'source_user_id')