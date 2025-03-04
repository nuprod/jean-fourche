# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.website_sale.controllers.main import PaymentPortal
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class PaymentPortal(PaymentPortal):

    def _validate_transaction_for_order(self, transaction, sale_order_id):
        super()._validate_transaction_for_order(transaction, sale_order_id)

        sale_order = request.env['sale.order'].sudo().browse(sale_order_id)
        account_payment_term_id = request.env['account.payment.term'].sudo().search([('payment_method_id', '=', transaction.payment_method_id.id)], limit=1)
        if sale_order:
            sale_order.payment_term_id = account_payment_term_id
        
        return