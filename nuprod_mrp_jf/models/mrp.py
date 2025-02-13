# -*- coding: utf-8 -*-

from odoo import models, fields, api


import logging

_logger = logging.getLogger(__name__)

class nuprod_mrp(models.Model):
    _inherit = 'mrp.production'

    def button_plan(self):
        
        procurement_group_id = self.procurement_group_id
        sale_order = self.env['sale.order'].search([('procurement_group_id', '=', procurement_group_id.id)])
        _logger.warning(sale_order)
        return super().button_plan()