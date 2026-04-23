from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    contains_dangerous_goods = fields.Boolean(
        string='Contains Dangerous Goods',
        compute='_compute_contains_dangerous_goods',
    )

    def _compute_contains_dangerous_goods(self):
        for package in self:
            # Priorité aux move_lines en cours (picking non encore validé) :
            # les quants ne sont pas encore physiquement dans le colis à ce stade.
            move_lines = self.env['stock.move.line'].search([
                ('result_package_id', '=', package.id),
                ('state', 'not in', ['done', 'cancel']),
                ('quantity', '>', 0),
            ])
            if move_lines:
                package.contains_dangerous_goods = any(
                    ml.product_id.dangerous_goods_line_ids
                    for ml in move_lines
                )
            else:
                # Fallback : quants réels en stock (après validation du picking)
                package.contains_dangerous_goods = any(
                    quant.product_id.dangerous_goods_line_ids
                    for quant in package.quant_ids
                )
