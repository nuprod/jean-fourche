# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
logger = logging.getLogger(__name__)


class res_company(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'
	
	facture_automatique = fields.Boolean("Facturer automatiquement une commande qui est payée et livrée")