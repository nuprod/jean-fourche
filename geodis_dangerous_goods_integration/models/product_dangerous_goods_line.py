from odoo import fields, models


class ProductDangerousGoodsLine(models.Model):
    _name = 'product.dangerous.goods.line'
    _description = 'Product Dangerous Goods Line'
    _order = 'no_onu, id'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
    )
    no_onu = fields.Char(string='No ONU', required=True)
    groupe_emballage = fields.Char(string='Groupe Emballage')
    classe_adr = fields.Char(string='Classe ADR')
    code_type_emballage = fields.Char(string='Code Type Emballage')
    nom_technique = fields.Char(string='Nom Technique')
    code_quantite = fields.Char(string='Code Quantite')
    danger_env = fields.Boolean(string='Danger Environnement')
    poids_matiere_dangereuse = fields.Float(string='Poids Matiere Dangereuse', required=True)
