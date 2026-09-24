from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aldais_shopify_new_partner_tag_id = fields.Many2one(
        comodel_name='res.partner.category',
        string='Tag for New Shopify Customers',
        config_parameter='aldais_shopify_integration.new_partner_tag_id',
        help=(
            'Tag set on the customers, companies and addresses created by the Shopify connector. '
            'If empty, the connector default tag "Integration / <integration name>" is used.'
        ),
    )
