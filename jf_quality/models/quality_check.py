# -*- coding: utf-8 -*-
from odoo import _, models


class QualityCheck(models.Model):
    _inherit = "quality.check"

    def do_alert(self):
        self.ensure_one()

        # Vals standard Odoo
        vals = {
            "check_id": self.id,
            "product_id": self.product_id.id,
            "product_tmpl_id": self.product_id.product_tmpl_id.id,
            "lot_id": self.lot_id.id,
            "user_id": self.user_id.id,
            "team_id": self.team_id.id,
            "company_id": self.company_id.id,
        }

        # 1) picking_id depuis le contrôle (si présent dans ton modèle)
        picking = getattr(self, "picking_id", False)
        if picking:
            vals["picking_id"] = picking.id

        # 2) fournisseur depuis le contrôle (si présent) sinon déduit via picking -> PO
        partner = getattr(self, "partner_id", False) or False
        purchase = False

        # picking.purchase_id est le cas standard sur réception
        if picking and getattr(picking, "purchase_id", False):
            purchase = picking.purchase_id
            if not partner:
                partner = purchase.partner_id

        if partner:
            vals["partner_id"] = partner.id

        # 3) purchase_id sur l’alerte (si ton champ custom existe)
        # (on ne met que si on a trouvé une PO)
        if purchase:
            vals["purchase_id"] = purchase.id

        alert = self.env["quality.alert"].create(vals)

        return {
            "name": _("Quality Alert"),
            "type": "ir.actions.act_window",
            "res_model": "quality.alert",
            "views": [(self.env.ref("quality_control.quality_alert_view_form").id, "form")],
            "res_id": alert.id,
            "context": {"default_check_id": self.id},
        }
