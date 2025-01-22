# Copyright 2019-2023 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details)
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    prepayment_bill = fields.Boolean(
        help="This Flag is set to True while creating a Down Payment on a Purchase Order.",
    )
