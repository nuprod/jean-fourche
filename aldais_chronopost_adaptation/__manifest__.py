{
    'name': 'Aldais - Chronopost 2Shop Adaptation',
    'summary': "Ajoute le support des offres Chronopost 2Shop (Direct, Retour, Europe, Retour Europe) au connecteur chronopost_shipping_integration",
    'description': """
        Complète le module Vraja "chronopost_shipping_integration" (webservice shippingMultiParcel v1)
        pour supporter les offres 2Shop demandées par Chronopost (ticket IT-17588, sept. 2026) :

        - 2Shop Direct (5X) et 2Shop Europe (6B) : étiquette d'envoi vers un point relais,
          via le webservice shippingMultiParcelV4.
        - 2Shop Retour (5Y) et 2Shop Retour Europe (6C) : étiquette de retour du client final
          vers l'adresse de retour de la société, générée depuis un assistant dédié
          (flux expéditeur/destinataire inversé par rapport à un envoi classique).
        - Recherche de points relais compatible 2Shop via recherchePointChronopostInter
          (avec le productCode réel 5X/6B), en plus de la recherche existante.

        Ce module n'altère pas le code de chronopost_shipping_integration : tout passe par
        de l'héritage (_inherit) et une bascule sur le code produit Chronopost, pour que le
        flux existant (Chrono13, Chrono Relais, etc.) continue de fonctionner à l'identique.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.0.0',
    'depends': ['chronopost_shipping_integration'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/chronopost_return_label_wizard_views.xml',
        'views/delivery_carrier_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
