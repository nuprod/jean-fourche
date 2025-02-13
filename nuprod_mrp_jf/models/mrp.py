# -*- coding: utf-8 -*-

from odoo import models, fields, api


import logging

_logger = logging.getLogger(__name__)

class nuprod_mrp(models.Model):
    _inherit = 'mrp.production'

    def button_plan(self):
        
        sale_order_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
        sale_order_ids.commitment_date = self.date_finished
        return super().button_plan()