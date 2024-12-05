from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    number_of_label = fields.Integer(string="Number Of Labels",default=1)