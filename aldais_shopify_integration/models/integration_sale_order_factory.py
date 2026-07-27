from odoo import models

from odoo.addons.integration.exceptions import ErrorStore as es


class IntegrationSaleOrderFactory(models.TransientModel):
    _inherit = 'integration.sale.order.factory'

    def _try_get_odoo_product(self, line, force_create=False):
        """
        Shopify-specific override: convert NotFoundExternalProduct (E110) and
        NotMappedFromExternal into UndefinedExternalProduct (E109) so that the
        base _prepare_order_line_vals fallback logic handles them transparently,
        without requiring any changes to the integration module.

        For non-Shopify integrations, the base behaviour is preserved.
        """
        if not self.integration_id.is_integration_shopify:
            return super()._try_get_odoo_product(line, force_create=force_create)

        try:
            return super()._try_get_odoo_product(line, force_create=force_create)
        except (es.NotFoundExternalProduct, es.NotMappedFromExternal) as ex:
            # Re-raise as UndefinedExternalProduct so the base _prepare_order_line_vals
            # catches it and uses the configured fallback product.
            raise es.UndefinedExternalProduct(str(ex))

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
