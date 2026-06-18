from itertools import groupby
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
            ('payment_method_code', '=', 'sdd'),
        ], order='date asc, currency_id asc')

        currency = request.env.company.currency_id
        upcoming_lines = []

        for (date, currency_id), group in groupby(
            upcoming_payments,
            key=lambda p: (p.date, p.currency_id.id)
        ):
            payments = list(group)
            total = sum(p.amount for p in payments)
            upcoming_lines.append({
                'date': format_date(request.env, date),
                'amount_str': format_amount(request.env, total, currency),
            })

        values['upcoming_sepa_lines'] = upcoming_lines
        return values