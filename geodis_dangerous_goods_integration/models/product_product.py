from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    dangerous_goods_line_ids = fields.One2many(
        'product.dangerous.goods.line',
        'product_id',
        string='Dangerous Goods Lines',
    )
