from odoo import fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalUpcomingPayment(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        all_partner_ids = request.env['res.partner'].sudo().search([
            ('commercial_partner_id', '=', commercial_partner.id)
        ]).ids

        payments = request.env['account.payment'].sudo().search([
            ('partner_id', 'in', all_partner_ids),
            ('state', '=', 'posted'),
            ('batch_payment_id', '!=', False),
            ('batch_payment_id.date', '>', fields.Date.today()),
            ('batch_payment_id.payment_method_id.code', '=', 'sepa_direct_debit'),
            ('batch_payment_id.state', 'in', ['draft', 'sent']),
        ])

        values['upcoming_sepa_amount'] = sum(payments.mapped('amount'))
        values['upcoming_sepa_currency'] = request.env.company.currency_id
        return values
