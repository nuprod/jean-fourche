from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    helpdesk_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket SAV',
        ondelete='set null',
        index=True,
    )
