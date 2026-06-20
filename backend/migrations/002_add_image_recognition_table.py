"""
Migration to add image_recognitions table.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create image_recognitions table."""
    op.create_table(
        'image_recognitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(512), nullable=True),
        sa.Column('recognition_type', sa.String(50), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_image_recognitions_id', 'image_recognitions', ['id'])
    op.create_index('ix_image_recognitions_user_id', 'image_recognitions', ['user_id'])


def downgrade():
    """Drop image_recognitions table."""
    op.drop_index('ix_image_recognitions_user_id')
    op.drop_index('ix_image_recognitions_id')
    op.drop_table('image_recognitions')