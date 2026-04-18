{
    'name': 'GEODIS Dangerous Goods Integration',
    'version': '17.0.1.0.0',
    'summary': 'Dynamic dangerous goods payload generation for Geodis shipments',
    'category': 'Inventory/Delivery',
    'depends': ['stock', 'product', 'geodis_shipping_integration'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/stock_quant_package_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
