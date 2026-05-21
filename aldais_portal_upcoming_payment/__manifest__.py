{
    'name': "Aldais Portal Prélèvement à venir",
    'description': "Affiche le montant des prélèvements SEPA à venir dans le portail client.",
    'author': "NUprod",
    'website': "http://www.nuprod.fr",
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'depends': ['portal', 'account_batch_payment'],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
