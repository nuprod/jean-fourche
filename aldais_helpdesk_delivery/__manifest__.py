{
    'name': 'Aldais - Livraison depuis ticket SAV',
    'summary': 'Création d\'une livraison sortante directement depuis un ticket d\'assistance SAV',
    'description': """
        Ajoute un bouton "Créer une livraison" sur les tickets SAV afin de générer
        automatiquement un bon de livraison sortant prérempli avec les informations du ticket.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.0.0',
    'depends': ['helpdesk', 'stock'],
    'data': [
        'views/helpdesk_ticket_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
