from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class NuprodSaleOrder(models.Model):
    _inherit = 'account.payment.term'

    payment_method_id = fields.Many2one('payment.method', string="Method de paiment associé", store=True)
    