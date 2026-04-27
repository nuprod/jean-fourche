{
    'name': 'Geodis - Information de livraison',
    'version': '17.0.1.0.0',
    'summary': 'Champ information de livraison sur partenaire et livraison, transmis à Geodis',
    'category': 'Inventory/Delivery',
    'depends': ['stock', 'contacts', 'geodis_shipping_integration'],
    'data': [
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
