from odoo import models


class IntegrationResPartnerProxy(models.TransientModel):
    _inherit = 'integration.res.partner.proxy'

    def _get_integration_tag(self):
        """
        For Shopify, use the tag selected in Settings > Aldais Shopify (if any) for the partners
        created by the connector (customer, company and addresses), instead of the
        "Integration / <name>" tag the connector creates by default.
        """
        if self.integration_id.is_integration_shopify:
            tag_id = self.env['ir.config_parameter'].sudo().get_param(
                'aldais_shopify_integration.new_partner_tag_id'
            )
            tag = self.env['res.partner.category'].browse(int(tag_id or 0)).exists()
            if tag:
                return tag
        return super()._get_integration_tag()
