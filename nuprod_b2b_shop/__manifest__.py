{
    'name': "nuprod_b2b_shop",
    'description': """
        This module add a new b2b shop for Odoo 17.0.
    """,
    'author': "NUprod",
    'website': "http://www.nuprod.fr",
    'version': '17.0.1.0',
    'category': 'Uncategorized',
    'depends': ['base', 'website_sale'],
    # 'data': [
    #     'views/portal_templates_view.xml',
    #     'views/auth_signup_login_templates_view.xml',
    # ], 
    # 'assets': {
    #     'web.assets_frontend': [
    #         'nuprod_shop_controller/static/src/css/*.css',
    #     ],
    #},
    'installable': True,  
    'application': False, 
    'auto_install': False,
}
