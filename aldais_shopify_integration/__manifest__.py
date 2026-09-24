{
    'name': 'Aldais - Shopify Integration Complements',
    'summary': 'Compléments Aldais pour le connecteur Shopify (integration_shopify)',
    'description': """
        Ajoute la récupération des metafields Shopify au niveau des lignes de commande
        et leur mapping vers des champs sale.order.line.

        Ajoute aussi la résolution automatique du point relais Chronopost à partir du
        metafield de commande "order.chronopost-relay-id" (posé par l'app Shopify de
        livraison en point relais) : la commande est automatiquement liée au bon
        chronopost.pickup.point à l'import, sans passer par "Get Locations"/"Set Location".

        Permet enfin de choisir, dans Paramètres > Aldais Shopify, l'étiquette posée sur les clients créés
        par le connecteur (par ex. "CLIENT B2C") à la place de "Integration / <nom>".

        Ce module n'altère pas les fichiers de integration_shopify : la requête GraphQL
        et les classes de ressources Shopify sont complétées via un monkey-patch (post_load),
        afin de rester compatible avec les mises à jour du connecteur.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.1.0',
    'depends': ['integration', 'integration_shopify', 'chronopost_shipping_integration'],
    'data': [
        'views/sale_integration_views.xml',
        'views/sale_order_cancel_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_load': 'post_load',
}
