from odoo import fields
from odoo.http import request
from odoo.tools.misc import format_amount, format_date
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalUpcomingPayment(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        all_partner_ids = request.env['res.partner'].sudo().search([
            ('commercial_partner_id', '=', commercial_partner.id)
        ]).ids

        upcoming_payments = request.env['account.payment'].sudo().search([
            ('partner_id', 'in', all_partner_ids),
            ('date', '>=', fields.Date.today()),
            ('state', 'not in', ['cancel']),
        ], order='date asc')

        currency = request.env.company.currency_id
        upcoming_lines = []
        for payment in upcoming_payments:
            upcoming_lines.append({
                'date': format_date(request.env, payment.date),
                'amount_str': format_amount(request.env, payment.amount, currency),
            })

        values['upcoming_sepa_lines'] = upcoming_lines
        return values
