"""Create users, conversations, messages and preferences.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17 09:42:23.674924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('pin_hash', sa.String(length=200), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("username ~ '^[a-z0-9_]{3,20}$'", name='username_format'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('recommended_item_ids', postgresql.ARRAY(sa.Integer()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role IN ('user', 'assistant')", name='message_role'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_table('preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('value', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
    sa.Column('superseded_by', sa.Integer(), nullable=True),
    sa.Column('source_message_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind <> 'allergy' OR value IN ('gluten', 'dairy', 'egg', 'peanut', 'tree_nut', 'soy', 'sesame', 'fish', 'shellfish', 'mustard')", name='pref_allergy_vocab'),
    sa.CheckConstraint("kind <> 'budget' OR (value ~ '^[0-9]+(\\.[0-9]{1,2})?$' AND value !~ '^[0.]+$')", name='pref_budget_number'),
    sa.CheckConstraint("kind <> 'diet' OR value IN ('vegetarian', 'vegan')", name='pref_diet_vocab'),
    sa.CheckConstraint("kind <> 'spice' OR value IN ('none', 'mild', 'medium', 'hot')", name='pref_spice_vocab'),
    sa.CheckConstraint("kind IN ('allergy', 'diet', 'dislike', 'like', 'budget', 'spice')", name='pref_kind'),
    sa.CheckConstraint("status IN ('active', 'superseded', 'removed')", name='pref_status'),
    sa.ForeignKeyConstraint(['source_message_id'], ['messages.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['superseded_by'], ['preferences.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preferences_user_id'), 'preferences', ['user_id'], unique=False)
    op.create_index('one_active_per_value', 'preferences', ['user_id', 'kind', 'value'], unique=True, postgresql_where=sa.text("status = 'active'"))
    op.create_index('one_active_single_valued', 'preferences', ['user_id', 'kind'], unique=True, postgresql_where=sa.text("status = 'active' AND kind IN ('budget', 'diet', 'spice')"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('one_active_single_valued', table_name='preferences', postgresql_where=sa.text("status = 'active' AND kind IN ('budget', 'diet', 'spice')"))
    op.drop_index('one_active_per_value', table_name='preferences', postgresql_where=sa.text("status = 'active'"))
    op.drop_index(op.f('ix_preferences_user_id'), table_name='preferences')
    op.drop_table('preferences')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_table('users')
