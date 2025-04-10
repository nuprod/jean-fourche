# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
logger = logging.getLogger(__name__)


class stock_picking(models.Model):
	_name = 'stock.picking'
	_inherit = 'stock.picking'
	
	def _action_done(self):
		res = super()._action_done()
		logger.info("_action_done")
		if self.env.user.company_id.facture_automatique:
			logger.info("facture auto")
			# on regarde si dans le champs origin on a le nom du sale order associé
			for p in self:
				if p.origin:
					sale = self.env["sale.order"].search([('name','=',p.origin)],limit=1)
					if len(sale)>0:
						if sale.amount_total == sum(sale.account_payment_ids.mapped('amount')) and not sale.force_invoiced:
							# alors on peut faire la facture et la poster
							invoiceable_lines = sale._get_invoiceable_lines()
							if any(not line.display_type for line in invoiceable_lines):
								invoices = sale._create_invoices()
								invoices.action_post()
		
		return res