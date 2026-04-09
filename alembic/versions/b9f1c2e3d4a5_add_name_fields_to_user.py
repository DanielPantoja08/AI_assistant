"""add name fields to user

Revision ID: b9f1c2e3d4a5
Revises: 3263a062d681
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b9f1c2e3d4a5'
down_revision: Union[str, Sequence[str], None] = '3263a062d681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("user", sa.Column("remember_name", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("user", "remember_name")
    op.drop_column("user", "last_name")
    op.drop_column("user", "first_name")
