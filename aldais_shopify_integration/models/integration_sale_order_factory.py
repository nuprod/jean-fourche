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
        # Capture the Shopify line name before super() so we can restore it
        # if the fallback product is used and Odoo's compute overwrites name.
        shopify_line_name = line_data.get('name') or ''

        res = super()._prepare_order_line_vals(order, line_data)

        if self.integration_id.is_integration_shopify:
            self._apply_shopify_fallback_name(res, shopify_line_name)
            self._apply_shopify_line_metafield_mappings(res, line_data)

        return res

    def _apply_shopify_fallback_name(self, vals, shopify_line_name):
        """
        When the fallback product is used, force the order line description to
        the original Shopify product name so the salesperson knows what was
        actually ordered.

        In Odoo 17, `sale.order.line.name` is a precomputed stored field. Even
        though the base integration module sets `vals['name']` in the fallback
        except-clause, Odoo's compute mechanism can overwrite it when
        `product_id` is set. We therefore re-apply the Shopify name here,
        directly on the vals dict before the record is created.
        """
        fallback_product = self.integration_id.fallback_product_id
        if not fallback_product:
            return
        if vals.get('product_id') != fallback_product.id:
            return
        if not shopify_line_name:
            return

        vals['name'] = shopify_line_name

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
