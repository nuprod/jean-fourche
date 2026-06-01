{
    'name': "Aldais Adaptation Portal Commande",
    'description': "Ajoute la colonne 'Date de livraison' (commitment_date) dans la liste des commandes du portail client.",
    'author': "Aldais",
    'website': "http://www.nuprod.fr",
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'depends': ['sale', 'sale_stock'],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
