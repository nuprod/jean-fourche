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

        upcoming_batches = request.env['account.batch.payment'].sudo().search([
            ('date', '>=', fields.Date.today()),
            ('payment_method_id.code', '=', 'sdd'),
            ('state', 'in', ['draft', 'sent']),
        ], order='date asc')

        currency = request.env.company.currency_id
        upcoming_lines = []
        for batch in upcoming_batches:
            payments = request.env['account.payment'].sudo().search([
                ('partner_id', 'in', all_partner_ids),
                ('batch_payment_id', '=', batch.id),
                ('state', 'not in', ['cancel']),
            ])
            if not payments:
                continue
            amount = sum(payments.mapped('amount'))
            upcoming_lines.append({
                'date': format_date(request.env, batch.date),
                'amount_str': format_amount(request.env, amount, currency),
            })

        values['upcoming_sepa_lines'] = upcoming_lines
        return values
