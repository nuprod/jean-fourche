# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    jf_supplier_return_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Type d'opération retour fournisseur",
        domain="[('code', '=', 'outgoing')]",
        config_parameter="jf_quality.supplier_return_picking_type_id",
        help="Type d'opération utilisé lors de la création d'un retour fournisseur depuis une alerte qualité.",
    )
