import logging
from odoo import fields
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class CustomerPortalUpcomingPayment(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        _logger.info("UPCOMING_PAYMENT | user=%s partner=%s commercial_partner=%s",
                     request.env.user.login, partner.id, commercial_partner.id)

        all_partner_ids = request.env['res.partner'].sudo().search([
            ('commercial_partner_id', '=', commercial_partner.id)
        ]).ids
        _logger.info("UPCOMING_PAYMENT | all_partner_ids=%s", all_partner_ids)

        # Test 1 : sans aucun filtre
        all_batches = request.env['account.batch.payment'].sudo().search([])
        _logger.info("UPCOMING_PAYMENT | total batches (aucun filtre)=%s", len(all_batches))
        for b in all_batches:
            _logger.info("UPCOMING_PAYMENT | batch id=%s name=%s date=%s state=%s method_id=%s method_code=%s",
                         b.id, b.name, b.date, b.state, b.payment_method_id.id, b.payment_method_id.code)

        # Test 2 : filtre date uniquement
        batches_date = request.env['account.batch.payment'].sudo().search([
            ('date', '>=', fields.Date.today()),
        ])
        _logger.info("UPCOMING_PAYMENT | batches avec date>=%s : %s", fields.Date.today(), len(batches_date))

        # Test 3 : filtre état uniquement
        batches_state = request.env['account.batch.payment'].sudo().search([
            ('state', 'in', ['draft', 'sent']),
        ])
        _logger.info("UPCOMING_PAYMENT | batches avec state in [draft,sent] : %s", len(batches_state))

        # Test 4 : filtre méthode uniquement
        batches_method = request.env['account.batch.payment'].sudo().search([
            ('payment_method_id.code', '=', 'sepa_direct_debit'),
        ])
        _logger.info("UPCOMING_PAYMENT | batches avec payment_method_id.code=sepa_direct_debit : %s", len(batches_method))

        upcoming_batches = request.env['account.batch.payment'].sudo().search([
            ('date', '>=', fields.Date.today()),
            ('payment_method_id.code', '=', 'sepa_direct_debit'),
            ('state', 'in', ['draft', 'sent']),
        ])
        _logger.info("UPCOMING_PAYMENT | today=%s batches found=%s ids=%s",
                     fields.Date.today(), len(upcoming_batches), upcoming_batches.ids)

        # Sans filtre partenaire pour voir tous les paiements dans ces batches
        all_payments_in_batches = request.env['account.payment'].sudo().search([
            ('batch_payment_id', 'in', upcoming_batches.ids),
        ])
        _logger.info("UPCOMING_PAYMENT | total payments in batches (sans filtre partenaire)=%s",
                     len(all_payments_in_batches))
        for p in all_payments_in_batches:
            _logger.info("UPCOMING_PAYMENT | payment id=%s partner_id=%s state=%s amount=%s",
                         p.id, p.partner_id.id, p.state, p.amount)

        payments = request.env['account.payment'].sudo().search([
            ('partner_id', 'in', all_partner_ids),
            ('batch_payment_id', 'in', upcoming_batches.ids),
            ('state', 'not in', ['cancel']),
        ])
        _logger.info("UPCOMING_PAYMENT | payments après filtre partenaire=%s", len(payments))

        amount = sum(payments.mapped('amount'))
        currency = request.env.company.currency_id
        _logger.info("UPCOMING_PAYMENT | montant final=%s currency=%s", amount, currency.name)
        values['upcoming_sepa_amount_str'] = format_amount(request.env, amount, currency)
        return values
