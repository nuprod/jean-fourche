# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

import logging
logger = logging.getLogger(__name__)

class sap_acquirer(models.Model):
    _name = 'sap.acquirer'
    
    name = fields.Char('Acquirer')

class PaymentAcquirer(models.Model):
    _inherit = 'payment.provider'
    
    def _get_selection(self):
        sap_providers = self.env['sap.acquirer'].search([]).mapped('name')
        res = zip(sap_providers,sap_providers)
        return list(res)
            
        
    provider = fields.Selection(related='provider_sap',string='Provider',readonly=False)
    provider_sap = fields.Selection(selection=_get_selection,string='Provider SAP')
    journal_id = fields.Many2one('account.journal',store=True)
    def _compute_journal_id(self):
        for acquirer in self:
            acquirer.journal_id = self.env['account.journal'].search([('acquirer_ids','in',acquirer.id)])



class AccountPayment(models.Model):

    _inherit = "account.payment"

    sale_id = fields.Many2one(
        "sale.order", "Sale", readonly=True, states={"draft": [("readonly", False)]}
    )


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'
    
    def _create_payment(self, add_payment_vals={}):
        ''' Create an account.payment record for the current payment.transaction.
        If the transaction is linked to some invoices, the reconciliation will be done automatically.
        :param add_payment_vals:    Optional additional values to be passed to the account.payment.create method.
        :return:                    An account.payment record.
        '''
        self.ensure_one()
        
        
        payment_vals = {
            'amount': self.amount,
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            #'payment_method_id': self.env.ref('payment.account_payment_method_electronic_in').id,
            'payment_method_id': self.acquirer_id.journal_id.inbound_payment_method_ids[0].id or self.env.ref('payment.account_payment_method_electronic_in').id,
            'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **add_payment_vals,
        }
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()
        
        # Track the payment to make a one2one.
        self.payment_id = payment
        
        if self.invoice_ids:
            self.invoice_ids.filtered(lambda move: move.state == 'draft')._post()
        
            (payment.line_ids + self.invoice_ids.line_ids)\
                .filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled)\
                .reconcile()
        
        return payment
    
