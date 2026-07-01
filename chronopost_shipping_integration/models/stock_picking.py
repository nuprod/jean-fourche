from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    chronopost_number_of_parcel = fields.Integer(string="Number Of Parcel", default=1)
