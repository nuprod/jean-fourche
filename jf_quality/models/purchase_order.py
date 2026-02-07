# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    quality_alert_ids = fields.One2many(
        comodel_name="quality.alert",
        inverse_name="purchase_id",
        string="Quality Alerts",
    )

    quality_alert_count = fields.Integer(
        compute="_compute_quality_alert_count",
        string="Quality Alerts Count",
    )

    def _compute_quality_alert_count(self):
        for po in self:
            po.quality_alert_count = len(po.quality_alert_ids)
