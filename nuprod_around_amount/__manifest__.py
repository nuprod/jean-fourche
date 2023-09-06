# -*- coding: utf-8 -*-
{
    'name': "nuprod_around_amount",

    'summary': """
        Module to modify total_amount and tax_amount in sale_order.py and tax_total.js,
        the goal is to get these amounts with wthe third decimal rounded to the next tenth""",

    'description': """
       Module to modify total_amount and tax_amount in sale_order.py and tax_total.js,
       the goal is to get these amounts with wthe third decimal rounded to the next tenth
    """,

    'author': "NUprod",
    'website': "http://www.nuprod.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nuprod_around_amount/static/src/js/*',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}