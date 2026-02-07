from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    quality_alert_ids = fields.One2many(
        "quality.alert",
        "supplier_id",
        string="Quality Alerts",
    )

    quality_alert_count = fields.Integer(
        compute="_compute_quality_alert_count"
    )

    def _compute_quality_alert_count(self):
        for partner in self:
            partner.quality_alert_count = len(partner.quality_alert_ids)