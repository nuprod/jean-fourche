# Copyright 2019-2023 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """The class is to created for inherited the model Res Config Settings"""
    _inherit = 'res.config.settings'

    po_deposit_default_product_id = fields.Many2one(
        'product.product',
        'PO Deposit Product',
        domain="[('type', '=', 'service')]",
        config_parameter='purchase_vendorbill_advance.po_deposit_default_product_id',
        help='Default product used for payment advances in purchase order')
