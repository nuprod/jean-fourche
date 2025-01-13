{
    'name': "nuprod_shop_controller",
    'description': """
        This module provides custom controllers for the shop.
        It does not include models, views, or data.
    """,
    'author': "NUprod",
    'website': "http://www.nuprod.fr",
    'version': '17.0.1.0',
    'category': 'Uncategorized',
    'depends': ['base', 'website_sale'],
    'data': [
        'views/portal_templates_view.xml',
        'views/auth_signup_login_templates_view.xml',
        'static/src/css/*.css',
    ], 
    'installable': True,  
    'application': False, 
    'auto_install': False,
}
