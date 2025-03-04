{
    'name': "nuprod_tacker_payment_method",
    'description': """
       This module tracks the payment method selected by the customer.
       The module add 1 new fields: payment_method_id in account.payment.term
    """,
    'author': "NUprod",
    'website': "http://www.nuprod.fr",
    'version': '17.0.1.0',
    'category': 'Uncategorized',
    'depends': ['base', 'sale', 'account'],
    'data': [
        # "views/sale_order_views.xml",
        "views/account_payment_term_views.xml"
    ], 
    'installable': True,  
}
