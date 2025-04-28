# -*- coding: utf-8 -*-

from odoo import models, fields, api


import logging

_logger = logging.getLogger(__name__)

class nuprod_mrp(models.Model):
    _inherit = 'mrp.production'

    def button_plan(self):
        for production in self:
            sale_order_id = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id
            sale_order_id.commitment_date = production.date_finished
        return super().button_plan()