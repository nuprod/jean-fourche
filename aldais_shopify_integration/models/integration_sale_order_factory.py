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
        Update order line values based on the order line custom attributes mappings
        (Shopify "line item properties") from the integration.
        """
        metafield_mappings = self.integration_id.order_line_metafield_mapping_ids

        if not metafield_mappings:
            return

        line_custom_attributes = line_data.get('custom_attributes') or {}

        if not line_custom_attributes:
            return

        for mapping in metafield_mappings:
            if mapping.metafield_key not in line_custom_attributes:
                continue

            metafield_value = line_custom_attributes[mapping.metafield_key]

            if mapping.metafield_type == 'boolean':
                metafield_value = True if metafield_value == 'true' else False

            vals[mapping.odoo_field_id.name] = metafield_value
