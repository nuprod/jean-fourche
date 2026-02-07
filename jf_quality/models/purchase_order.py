from odoo import fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    quality_alert_ids = fields.One2many(
        "quality.alert",
        "purchase_id",
        string="Quality Alerts",
    )

    quality_alert_count = fields.Integer(
        compute="_compute_quality_alert_count"
    )

    def _compute_quality_alert_count(self):
        for po in self:
            po.quality_alert_count = len(po.quality_alert_ids)