"""make_customer_kyc_id_required_in_company_kyc

Revision ID: 7a4876a11b6e
Revises: 3edaa73deca3
Create Date: 2026-05-09 16:07:41.277906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a4876a11b6e'
down_revision: Union[str, Sequence[str], None] = '3edaa73deca3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove dev/test rows that have no individual KYC linked (created before Option B was enforced)
    op.execute('DELETE FROM "COMPANY_KYC" WHERE customer_kyc_id IS NULL')
    op.alter_column('COMPANY_KYC', 'customer_kyc_id', nullable=False)


def downgrade() -> None:
    op.alter_column('COMPANY_KYC', 'customer_kyc_id', nullable=True)
