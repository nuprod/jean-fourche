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

    def _import_external_product(self, template_ids, try_to_map=True, raise_error=True):
        """
        Shopify-specific override: force raise_error=False so that import errors
        (e.g. E113 UniqueViolation when multiple "customized" products share an
        empty external_reference='') are silently collected instead of being
        re-raised as ApiImportError.

        When raise_error=False, _import_external_product returns empty results on
        error, which causes _try_get_odoo_product to raise E110 naturally.
        The factory then converts E110 to UndefinedExternalProduct so the
        configured fallback product is used.

        For non-Shopify integrations the base behaviour is preserved.
        """
        if self.is_integration_shopify:
            raise_error = False
        return super()._import_external_product(
            template_ids, try_to_map=try_to_map, raise_error=raise_error,
        )

    def _try_get_odoo_product(self, product_data, force_create=False):
        """
        Shopify-specific override: convert unexpected errors during product
        auto-creation (e.g. ValidationError on a "customized" product without
        SKU/reference) into NotFoundExternalProduct (E110) so the factory can
        redirect to the configured fallback product.

        UniqueViolation errors (E113) are already suppressed upstream by
        _import_external_product (raise_error=False), so this handler only
        needs to cover auto-creation failures from import_product().

        For non-Shopify integrations the base behaviour is preserved.
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
            # Unexpected failure during auto-creation of a Shopify product
            # (e.g. ValidationError because the product has no SKU/reference).
            # Convert to E110 so the factory fallback logic is triggered.
            _logger.warning(
                '%s: Auto-creation of Shopify product "%s" (template=%s, variant=%s) '
                'failed: %s. Fallback product will be used if configured.',
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
