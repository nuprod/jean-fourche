# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):

    @http.route('/integration/integration_ecommerce_fields_onboarding', auth='user', type='json')
    def integration_ecommerce_fields_onboarding(self):
        """
        Returns the `banner` for the integration ecommerce fields onboarding panel.
        Always displays the banner.
        """
        return {
            'html': request.env['ir.qweb']._render('integration.integration_ecommerce_fields_onboarding_panel')
        }

    @http.route('/integration/integration_ecommerce_fields_mapping_onboarding', auth='user', type='json')
    def integration_ecommerce_fields_mapping_onboarding(self):
        """
        Returns the `banner` for the integration ecommerce fields mapping onboarding panel.
        Always displays the banner.
        """
        return {
            'html': request.env['ir.qweb']._render('integration.integration_ecommerce_fields_mapping_onboarding_panel')
        }
