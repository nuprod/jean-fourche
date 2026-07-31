# See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductPublicCategory(models.Model):
    _name = 'product.public.category'
    _inherit = ['product.public.category', 'integration.model.mixin']

    def to_export_format(self, integration: 'models.Model'):
        self.ensure_one()

        if integration.is_integration_shopify:
            return {
                'name': self.name,
            }

        return super(ProductPublicCategory, self).to_export_format(integration)
