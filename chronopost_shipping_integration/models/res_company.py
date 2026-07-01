from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_chronopost_shipping_provider = fields.Boolean(copy=False, string="Are You Use chronopost Shipping Provider.?",
                                                help="If use chronopost shipping provider than value set TRUE.",
                                                default=False)
    chronopost_api_url = fields.Char(string="API URL", copy=False, default="https://ws.chronopost.fr")
    chronopost_account_number = fields.Char(String="Account Number", copy=False)
    chronopost_password = fields.Char(string="Password", copy=False)
