# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_geodis_shipping_provider = fields.Boolean(copy=False, string="Are You Using GEODIS",
                                                  help="If use GEODIS shipping Integration than value set "
                                                       "TRUE.",
                                                  default=False)
    geodis_api_url = fields.Char(string='GEODIS API URL')
    geodis_id = fields.Char(string='GEODIS ID')
    geodis_api_key = fields.Char(string='GEODIS API KEY')
    agency_code = fields.Char(string='Ordering agency code')
    customer_account = fields.Char(string='Customer Account')

