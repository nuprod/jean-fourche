# -*- coding: utf-8 -*-pack
{       # App information
        'name': 'GEODIS Shipping Integration',
        'category': 'Website',
        'version': '1.0.0',
        'summary': """Shipping integration with Odoo is a crucial aspect of optimizing and streamlining business logistics. Odoo, a comprehensive business management software, allows seamless integration with various shipping carriers to enhance the efficiency of the shipping process. You can perform various operations like get Live shipping rate,Generate Shipping labels, Track Shipment,You can cancel the shipments too. You can find out our other modules like Vraja Shipping Integration, vraja technologies, vraja shipping, France shipping integration by vraja technologies, FR Shipping Integration, odoo, chronopost, transsmart, relaiscolis, relais colis, shipstation, laposte, colis prive, colisprive, shipengine, delivengo, springgds, spring gds, glsfrance, gls, glsshipping, dpd, dpdfrance, tnt, tntfrance, myschenker, francedbschenker, dbschenker, geodis, colissimo, bpost, mondialrelay, mondial relay.""",
        'description': """GEODIS Shipping Integration""",
        'depends': ['delivery','stock','stock_delivery'],
        'data': [
            'views/res_company.xml',
            'views/delivery_carrier.xml',
            'views/stock_picking.xml',
        ],

        'images': ['static/description/cover.jpg'],

        'author': 'Vraja Technologies',
        'maintainer': 'Vraja Technologies',
        'website':'www.vrajatechnologies.com',
        'demo': [],
        'live_test_url': 'https://www.vrajatechnologies.com/contactus',
        'installable': True,
        'application': True,
        'auto_install': False,
        'price': '321',
        'currency': 'EUR',
        'license': 'OPL-1',
}
