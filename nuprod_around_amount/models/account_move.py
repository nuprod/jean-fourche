# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class nuprod_account_move(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state')
    def _compute_amount(self):
        for move in self:
            total_untaxed, total_untaxed_currency = 0.0, 0.0
            total_tax, total_tax_currency = 0.0, 0.0
            total_residual, total_residual_currency = 0.0, 0.0
            total, total_currency = 0.0, 0.0

            for line in move.line_ids:
                # _logger.warning(
                #     "Quentin line.move_id.line_ids - line %s", line.balance)
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            sign = move.direction_sign
            last_digit = (total_residual_currency * 1000) % 10
            # je fais un * 1000 / 1000 afin d'éviter les comportements étranges de python
            if last_digit > 0:
                total_tax = ((total_tax * 1000) + last_digit) / 1000
                total_tax_currency = ((total_tax_currency * 1000) + last_digit) / 1000
                total_residual = ((total_residual * 1000) - last_digit) / 1000
                total_residual_currency = ((total_residual_currency * 1000) - last_digit) / 1000
                total = ((total * 1000) + last_digit) / 1000
                total_currency = ((total_currency * 1000) + last_digit) / 1000
            
            move.amount_untaxed = sign * total_untaxed_currency
            move.amount_tax = sign * total_tax_currency
            move.amount_total = sign * total_currency
            move.amount_residual = -sign * total_residual_currency
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total)

# class nuprod_account_move_line(models.Model):
#     _inherit = 'account.move.line'
    
#     @api.depends('move_id')
#     def _compute_balance(self):
        
#         for line in self:
#             _logger.warning(
#                     line.move_id.is_invoice(include_receipts=True))
#             _logger.warning(
#                     "Quentin line.move_id.line_ids - line %s", line.move_id.line_ids)
#             if line.display_type in ('line_section', 'line_note'):
#                 line.balance = False
#             elif not line.move_id.is_invoice(include_receipts=True):
#                 # Only act as a default value when none of balance/debit/credit is specified
#                 # balance is always the written field because of `_sanitize_vals`
#                 _logger.warning(
#                     "Quentin line.move_id.line_ids - line %s", -sum((line.move_id.line_ids - line).mapped('balance')))
#                 line.balance = -sum((line.move_id.line_ids - line).mapped('balance'))
#             else:
#                 line.balance = 0