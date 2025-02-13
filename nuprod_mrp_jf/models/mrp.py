# -*- coding: utf-8 -*-

from odoo import models, fields, api


import logging

_logger = logging.getLogger(__name__)

class nuprod_mrp(models.Model):
    _inherit = 'mrp.production'

    def button_plan(self):
        _logger.warning('button_plan')
        return super().button_plan()