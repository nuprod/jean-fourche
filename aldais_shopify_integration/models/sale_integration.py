import logging

from odoo import fields, models

from odoo.addons.integration.exceptions import ErrorStore as es

_logger = logging.getLogger(__name__)


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

    def _try_get_odoo_product(self, product_data, force_create=False):
        """
        Shopify-specific override: convert unexpected errors during product resolution
        (e.g. UniqueViolation on empty SKU, or product auto-creation failure for
        "customized" products without a reference) into NotFoundExternalProduct (E110),
        so the factory can redirect to the fallback product.

        For non-Shopify integrations, the base behaviour is preserved.
        """
        if not self.is_integration_shopify:
            return super()._try_get_odoo_product(product_data, force_create=force_create)

        complex_variant_code = product_data.get('product_id', '')
        template_code = variant_code = None
        if complex_variant_code:
            template_code, variant_code = self.adapter._parse_product_external_code(
                complex_variant_code
            )

        try:
            return super()._try_get_odoo_product(product_data, force_create=force_create)
        except (es.UndefinedExternalProduct, es.NotFoundExternalProduct, es.NotMappedFromExternal):
            # Expected integration errors — let them propagate as-is.
            raise
        except Exception as ex:
            # Shopify-specific: unexpected failure during product resolution.
            # Examples:
            #   - ApiImportError wrapping a UniqueViolation (E113) when multiple
            #     customised products share an empty external_reference=''.
            #   - ValidationError during auto-creation of a product without SKU/reference.
            # Convert to E110 so the factory's Shopify _try_get_odoo_product override
            # can redirect to the configured fallback product.
            _logger.warning(
                '%s: Failed to resolve Shopify product "%s" (template=%s, variant=%s): %s. '
                'Fallback product will be used if configured.',
                self.name,
                product_data.get('name', 'null'),
                template_code,
                variant_code,
                str(ex),
            )
            es.raise_error(
                err_code='E110',
                integration_name=self.name,
                product_id=template_code,
                variant_id=variant_code,
                product_name=product_data.get('name', 'null'),
                product_reference=product_data.get('reference', 'null'),
            )
