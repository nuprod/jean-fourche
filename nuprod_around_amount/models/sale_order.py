# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class nuprod_sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            amount_tax = sum(order_lines.mapped('price_tax'))
            amount_total = amount_untaxed + amount_tax
            last_digit = (amount_total * 1000) % 10

            order.amount_untaxed = amount_untaxed
            order.amount_tax = ((amount_tax * 1000) - last_digit) / 1000
            order.amount_total = ((amount_total * 1000) - last_digit) / 1000
