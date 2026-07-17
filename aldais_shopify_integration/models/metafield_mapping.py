from odoo import fields, models

from odoo.addons.integration_shopify.models.metafield_mapping import MODEL_MAPPING

# Route the new 'order_line' metafield type to sale.order.line.
MODEL_MAPPING['order_line'] = 'sale.order.line'


class ExternalMetafield(models.Model):
    _inherit = 'external.metafield'

    type = fields.Selection(
        selection_add=[('order_line', 'Order Line')],
        ondelete={'order_line': 'cascade'},
    )
