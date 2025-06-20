# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict
import json
import logging
from datetime import date

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def button_plan(self):
        for production in self:
            sale_order_id = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id
            sale_order_id.commitment_date = production.date_finished
        return super().button_plan()


class StockMove(models.Model):
    _inherit = 'stock.move'

    forecast_calculation_date = fields.Datetime('Last calculation date forecast')

    @api.depends(
        'product_id', 'product_qty', 'picking_type_id', 'quantity', 'priority',
        'state', 'product_uom_qty', 'location_id'
    )
    def _compute_forecast_information(self):
        self.forecast_availability = False
        self.forecast_expected_date = False

        self.product_id.fetch(['type', 'uom_id'])

        not_product_moves = self.filtered(lambda move: move.product_id.type != 'product')
        for move in not_product_moves:
            move.forecast_availability = move.product_qty

        product_moves = self - not_product_moves
        outgoing_unreserved_moves_per_warehouse = defaultdict(set)
        now = fields.Datetime.now()

        def key_virtual_available(move, incoming=False):
            warehouse = move.location_dest_id.warehouse_id if incoming else move.location_id.warehouse_id
            warehouse_id = warehouse.id if warehouse else False
            return warehouse_id, max(move.date or now, now)

        prefetch_virtual_available = defaultdict(set)
        virtual_available_dict = {}

        for move in product_moves:
            if move._is_consuming() and move.state == 'draft':
                key = key_virtual_available(move)
                if key[0]:
                    prefetch_virtual_available[key].add(move.product_id.id)
            elif move.picking_type_id.code == 'incoming':
                key = key_virtual_available(move, incoming=True)
                if key[0]:
                    prefetch_virtual_available[key].add(move.product_id.id)

        for key_context, product_ids in prefetch_virtual_available.items():
            read_res = self.env['product.product'].browse(product_ids).with_context(
                warehouse=key_context[0], to_date=key_context[1]
            ).read(['virtual_available'])
            virtual_available_dict[key_context] = {
                res['id']: res['virtual_available'] for res in read_res
            }

        for move in product_moves:
            if move._is_consuming():
                if move.state == 'assigned':
                    move.forecast_availability = move.product_uom._compute_quantity(
                        move.quantity, move.product_id.uom_id, rounding_method='HALF-UP')
                elif move.state == 'draft':
                    key = key_virtual_available(move)
                    if key in virtual_available_dict:
                        move.forecast_availability = virtual_available_dict[key][move.product_id.id] - move.product_qty
                elif move.state in ('waiting', 'confirmed', 'partially_available'):
                    wh = move.location_id.warehouse_id
                    if wh:
                        outgoing_unreserved_moves_per_warehouse[wh].add(move.id)
            elif move.picking_type_id.code == 'incoming':
                key = key_virtual_available(move, incoming=True)
                if key in virtual_available_dict:
                    forecast_availability = virtual_available_dict[key][move.product_id.id]
                    if move.state == 'draft':
                        forecast_availability += move.product_qty
                    move.forecast_availability = forecast_availability

        for warehouse, moves_ids in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:
                continue
            moves = self.browse(moves_ids)
            moves_per_location = defaultdict(lambda: self.env['stock.move'])

            for move in moves:
                moves_per_location[move.location_id] |= move

            for location, mvs in moves_per_location.items():
                today = fields.Date.today()
                cache = self.env['stock.forecast.cache'].search([
                    ('warehouse_id', '=', warehouse.id),
                    ('location_id', '=', location.id),
                    ('date', '=', today)
                ], limit=1)

                if cache and cache.data:
                    try:
                        decoded = json.loads(cache.data)
                        forecast_info = {
                            int(k): tuple(v) for k, v in decoded.items()
                        }
                    except Exception as e:
                        _logger.warning("Failed to load forecast cache for warehouse %s, location %s: %s",
                                        warehouse.name, location.name, str(e))
                        forecast_info = {}
                else:
                    forecast_info_raw = mvs._get_forecast_availability_outgoing(warehouse, location)
                    serializable_data = {
                        move.id: [
                            forecast_info_raw[move][0],
                            forecast_info_raw[move][1].strftime('%Y-%m-%d %H:%M:%S') if forecast_info_raw[move][1] else None
                        ]
                        for move in mvs
                    }

                    self.env['stock.forecast.cache'].create({
                        'warehouse_id': warehouse.id,
                        'location_id': location.id,
                        'date': today,
                        'data': json.dumps(serializable_data),
                    })

                    forecast_info = {
                        int(move_id): (val[0], fields.Datetime.from_string(val[1]) if val[1] else False)
                        for move_id, val in serializable_data.items()
                    }


                for move in mvs:
                    move.forecast_availability, move.forecast_expected_date = forecast_info.get(
                        move.id, (False, False)
                    )
