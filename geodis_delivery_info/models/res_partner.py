from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_info = fields.Text(
        string="Information de livraison",
        help="Consigne de livraison reprise automatiquement sur les livraisons de ce partenaire.",
    )
