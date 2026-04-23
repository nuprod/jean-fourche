{
    'name': 'JF Base',
    'summary': 'Ajustements de base pour Jean Fourche',
    'description': """
        Module de base contenant tous les ajustements liés au client Jean Fourche
        ne nécessitant pas la création d'un module complet.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.0.0',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
