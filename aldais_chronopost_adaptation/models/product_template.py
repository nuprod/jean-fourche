# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    chronopost_customs_description = fields.Char(
        string="Désignation douane Chronopost (EN)",
        help="Description en anglais, précise et non générique, utilisée dans la balise <content1> "
             "des étiquettes Chronopost 2Shop Europe / 2Shop Retour Europe (exigence Chronopost, "
             "ex. \"leather heels for women\" et non \"shoes\"). Obligatoire pour tout envoi 2Shop "
             "vers/depuis l'UE si ce produit est l'article principal du colis.",
    )
