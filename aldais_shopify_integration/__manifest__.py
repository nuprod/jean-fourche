{
    'name': 'Aldais - Shopify Integration Complements',
    'summary': 'Compléments Aldais pour le connecteur Shopify (integration_shopify)',
    'description': """
        Ajoute la récupération des metafields Shopify au niveau des lignes de commande
        et leur mapping vers des champs sale.order.line.

        Ce module n'altère pas les fichiers de integration_shopify : la requête GraphQL
        et les classes de ressources Shopify sont complétées via un monkey-patch (post_load),
        afin de rester compatible avec les mises à jour du connecteur.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.0.0',
    'depends': ['integration', 'integration_shopify'],
    'data': [
        'views/sale_integration_views.xml',
        'views/sale_order_cancel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_load': 'post_load',
}
