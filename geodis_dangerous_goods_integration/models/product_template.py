from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dangerous_goods_line_ids = fields.One2many(
        'product.dangerous.goods.line',
        'product_tmpl_id',
        string='Dangerous Goods Lines',
    )
