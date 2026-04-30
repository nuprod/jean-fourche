from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_force_confirm(self):
        """Aligne les quantités des lignes de mouvement avec les quantités demandées."""
        for picking in self:
            for move in picking.move_ids:
                if move.quantity != move.product_uom_qty:
                    move.quantity = move.product_uom_qty