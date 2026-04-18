from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    contains_dangerous_goods = fields.Boolean(
        string='Contains Dangerous Goods',
        compute='_compute_contains_dangerous_goods',
    )

    def _compute_contains_dangerous_goods(self):
        for package in self:
            package.contains_dangerous_goods = any(
                quant.product_id.product_tmpl_id.dangerous_goods_line_ids
                for quant in package.quant_ids
            )
