"""
Migration to add output_data column to workflow_executions table.
This fixes: no such column: workflow_executions.output_data
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add output_data column to workflow_executions table."""
    op.add_column('workflow_executions', sa.Column('output_data', sa.JSON(), nullable=True))


def downgrade():
    """Remove output_data column from workflow_executions table."""
    op.drop_column('workflow_executions', 'output_data')
