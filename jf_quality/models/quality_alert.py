from odoo import api, models

class QualityAlert(models.Model):
    _inherit = "quality.alert"

    @api.onchange("picking_id")
    def _onchange_picking_id_set_partner(self):
        for alert in self:
            partner = alert._get_partner_from_picking(alert.picking_id)
            if partner:
                alert.partner_id = partner

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_partner_from_picking()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "picking_id" in vals:
            self._sync_partner_from_picking()
        return res

    def _sync_partner_from_picking(self):
        for alert in self:
            if alert.picking_id and not alert.partner_id:
                partner = alert._get_partner_from_picking(alert.picking_id)
                if partner:
                    alert.partner_id = partner.id

    def _get_partner_from_picking(self, picking):
        if not picking:
            return False
        # lien direct PO
        if getattr(picking, "purchase_id", False):
            return picking.purchase_id.partner_id
        # fallback via moves
        move = picking.move_ids.filtered(lambda m: m.purchase_line_id)[:1]
        if move:
            return move.purchase