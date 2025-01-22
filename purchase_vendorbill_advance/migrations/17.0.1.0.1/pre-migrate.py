# Copyright 2024 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
SELECT id
FROM   ir_config_parameter
WHERE  KEY = 'purchase.default_deposit_product_id';
    """
    )
    param_exists = cr.fetchall()
    if param_exists:
        cr.execute(
            """
UPDATE ir_config_parameter
SET    KEY = 'purchase_vendorbill_advance.po_deposit_default_product_id'
WHERE  KEY = 'purchase.default_deposit_product_id';
"""
        )
        _logger.info("""Updated the Config Parameter for purchase_vendorbill_advance""")