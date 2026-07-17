from odoo import fields, models


class SaleIntegration(models.Model):
    _inherit = 'sale.integration'

    order_line_metafield_mapping_ids = fields.One2many(
        comodel_name='integration.metafield.mapping',
        inverse_name='integration_id',
        string='Order Line Metafield Mappings',
        domain=[('type', '=', 'order_line')],
        help=(
            'Defines the mappings between the order line metafields in the external system and the '
            'fields in Odoo.'
        ),
    )
