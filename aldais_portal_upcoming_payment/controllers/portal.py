from odoo import fields
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalUpcomingPayment(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        all_partner_ids = request.env['res.partner'].sudo().search([
            ('commercial_partner_id', '=', commercial_partner.id)
        ]).ids

        upcoming_batches = request.env['account.batch.payment'].sudo().search([
            ('date', '>=', fields.Date.today()),
            ('payment_method_id.code', '=', 'sepa_direct_debit'),
            ('state', 'in', ['draft', 'sent']),
        ])

        payments = request.env['account.payment'].sudo().search([
            ('partner_id', 'in', all_partner_ids),
            ('batch_payment_id', 'in', upcoming_batches.ids),
            ('state', 'not in', ['cancel']),
        ])

        amount = sum(payments.mapped('amount'))
        currency = request.env.company.currency_id
        values['upcoming_sepa_amount_str'] = format_amount(request.env, amount, currency)
        return values
