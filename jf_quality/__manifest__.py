# -*- coding: utf-8 -*-
{
    'name': "Jeanfourche - Amélioration qualité",

    'summary': "Amélioration du module qualité",

    'description': """
Amélioration du module qualité
07/02 : Affectation automatique du fournisseur lors de l'affectation d'un transfert dans la Quality Alert
07/02 : Affectation des Quality alert aux commandes d'achat
07/02 : Affichage des Quality alert associées au fournisseur dans la fiche fournisseur
    """,

    'author': "Fabien Lauroua",
    'website': "https://djungle.eu",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','quality_control'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order',
        'views/res_partner',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

