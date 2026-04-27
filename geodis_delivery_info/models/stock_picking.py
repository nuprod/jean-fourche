from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_info = fields.Text(
        string="Information de livraison",
        help=(
            "Consigne de livraison. Alimentée automatiquement depuis le partenaire "
            "ou la société parente, modifiable manuellement. "
            "Transmise à Geodis dans le champ instructionLivraison."
        ),
    )

    def _compute_delivery_info_from_partner(self, partner):
        """
        Retourne l'information de livraison selon la règle de priorité :
        1. Valeur sur le partenaire/adresse sélectionné
        2. Valeur sur le partenaire parent (société)
        3. Chaîne vide
        """
        if not partner:
            return ''
        if partner.delivery_info:
            return partner.delivery_info
        if partner.parent_id and partner.parent_id.delivery_info:
            return partner.parent_id.delivery_info
        return ''

    @api.onchange('partner_id')
    def _onchange_partner_id_delivery_info(self):
        self.delivery_info = self._compute_delivery_info_from_partner(self.partner_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-alimentation uniquement si delivery_info non explicitement fourni
            if 'partner_id' in vals and 'delivery_info' not in vals:
                partner = self.env['res.partner'].browse(vals['partner_id'])
                vals['delivery_info'] = self._compute_delivery_info_from_partner(partner)
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        # Si le partenaire change, recalculer l'information de livraison
        if 'partner_id' in vals:
            for record in self:
                record.delivery_info = record._compute_delivery_info_from_partner(record.partner_id)
        return result
