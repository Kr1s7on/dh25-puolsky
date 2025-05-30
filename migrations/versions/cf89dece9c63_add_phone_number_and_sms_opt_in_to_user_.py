"""Add phone_number and sms_opt_in to User model

Revision ID: cf89dece9c63
Revises: 
Create Date: 2025-05-18 10:17:41.319324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf89dece9c63'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('LOW_STOCK', 'MISSED_DOSE', 'OVERDUE_DOSE', name='notificationtype'), nullable=False),
    sa.Column('message', sa.String(length=256), nullable=False),
    sa.Column('status', sa.Enum('UNREAD', 'READ', 'SNOOZED', 'ACKNOWLEDGED', name='notificationstatus'), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('snoozed_until', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('resident_id', sa.Integer(), nullable=True),
    sa.Column('inventory_item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ),
    sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('users', sa.Column('phone_number', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('sms_opt_in', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'sms_opt_in')
    op.drop_column('users', 'phone_number')
    op.drop_table('notifications')
    # ### end Alembic commands ###
