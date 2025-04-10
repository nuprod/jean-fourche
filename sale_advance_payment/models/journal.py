# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
logger = logging.getLogger(__name__)


class account_journal(models.Model):
	_name = 'account.journal'
	_inherit = 'account.journal'
	
	acquirer_ids = fields.Many2many('payment.provider',string='Intermédiaires de paiement')
	
	def create_acquirer(self):
		
		for pm in self.inbound_payment_method_ids:
			logger.info(pm)
			if pm.code not in self.env['sap.acquirer'].search([]).mapped('name'):
				self.env['sap.acquirer'].create({'name': pm.code})
			
			
			value = {
				'name': pm.name,
				'provider': pm.code,
				'state': 'enabled',
				'journal_id': self.id,
			}
			logger.info(value)
			pa_ids = self.env['payment.acquirer'].search([('name','=',pm.name),('provider','=',pm.code)])
			if len(pa_ids) == 0:
				pa_ids = self.env['payment.acquirer'].create(value)
			else:
				pa_ids.write(value)
				
			if pa_ids not in self.acquirer_ids:
				self.acquirer_ids += pa_ids