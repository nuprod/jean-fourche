from odoo import models


class IntegrationSaleOrderFactory(models.TransientModel):
    _inherit = 'integration.sale.order.factory'

    def _prepare_order_line_vals(self, order, line_data):
        res = super()._prepare_order_line_vals(order, line_data)

        if self.integration_id.is_integration_shopify:
            self._apply_shopify_line_metafield_mappings(res, line_data)

        return res

    def _apply_shopify_line_metafield_mappings(self, vals, line_data):
        """
        Update order line values based on the order line metafield mappings from the integration.
        """
        metafield_mappings = self.integration_id.order_line_metafield_mapping_ids

        if not metafield_mappings:
            return

        line_metafields = line_data.get('metafields') or []

        if not line_metafields:
            return

        for mapping in metafield_mappings:
            for line_metafield in line_metafields:
                if line_metafield.get('key') == mapping.metafield_key:
                    metafield_value = line_metafield.get('value')

                    if mapping.metafield_type == 'boolean':
                        metafield_value = True if metafield_value == 'true' else False

                    vals[mapping.odoo_field_id.name] = metafield_value
                    break
