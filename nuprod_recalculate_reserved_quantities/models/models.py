# -*- coding: utf-8 -*-

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class NuprodStockQuant(models.Model):
    _inherit = 'stock.quant'

    def recalculate_reserved_quantities(self):
        for quant in self:         
            domain = [
                ('location_id', '=', quant.location_id.id),
                ('product_id', '=', quant.product_id.id),
                ('state', 'not in', ['done', 'cancel']),
                ('lot_id', '=', quant.lot_id.id),
            ]
            if quant.package_id:
                domain.append(('package_id', '=', quant.package_id.id))
            else:
                domain.append(('package_id', '=', False))
            
            # Search for stock.move.line records
            move_lines = self.env['stock.move.line'].search(domain)

            # Sum up the reserved quantities
            reserved_quantity = sum(move_lines.mapped('quantity'))

            # Update the reserved quantity on the quant
            quant.sudo().write({'reserved_quantity': reserved_quantity})


    class NuprodStockLot(models.Model):
        _inherit = 'stock.lot'

        def recalculate_reserved_quantities(self):
            StockMoveLine = self.env['stock.move.line']
            for lot in self:
                quants = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
                for quant in quants:
                    domain = [
                        ('location_id', '=', quant.location_id.id),
                        ('product_id', '=', quant.product_id.id),
                        ('state', 'in', ['assigned', 'confirmed', 'partially_available']),
                        ('lot_id', '=', quant.lot_id.id),
                    ]
                    if quant.package_id:
                        domain.append(('package_id', '=', quant.package_id.id))
                    else:
                        domain.append(('package_id', '=', False))

                    reserved_quantity = sum(StockMoveLine.search(domain).mapped('quantity'))
                    _logger.info('Reserved quantity for quant %s: %s', quant.id, reserved_quantity)
                    quant.sudo().write({'reserved_quantity': reserved_quantity})


