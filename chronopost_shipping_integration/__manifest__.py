# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'Chronopost Shipping Integration',
    'category': 'Website',
    'version': '17.0.1.0',
    'summary': '''The Chronopost Shipping Integration for Odoo connects Odoo ERP with Chronopost, enabling businesses to automate parcel shipping operations directly from Odoo.
With this module, you can create Chronopost shipments, generate shipping labels, and track deliveries without logging into external carrier portals. The entire workflow—from Sales Order to Delivery Order to Chronopost label and tracking—is handled seamlessly inside Odoo.
Generate Chronopost shipments directly from Odoo Delivery Orders
Automatically send shipment data to Chronopost
Supports domestic & international parcel shipping
Eliminates manual shipment creation on Chronopost systems
Generate Chronopost shipping labels directly inside Odoo
Print-ready labels attached to delivery orders
Faster packing and dispatch process
Reduced labeling and shipping errors
Fully integrated with Odoo Inventory

Supports:
Pick-Pack-Ship workflow
Single & multi-warehouse environments
Suitable for high-volume shipping operations

This integration is ideal for France-based and EU businesses that rely on Chronopost for fast, reliable domestic and international deliveries.
At 𝗩𝗿𝗮𝗷𝗮 𝗧𝗲𝗰𝗵𝗻𝗼𝗹𝗼𝗴𝗶𝗲𝘀, we continue to innovate as a globally renowned 𝘀𝗵𝗶𝗽𝗽𝗶𝗻𝗴 𝗶𝗻𝘁𝗲𝗴𝗿𝗮𝘁𝗼𝗿 𝗮𝗻𝗱 𝗢𝗱𝗼𝗼 𝗰𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗮𝘁𝗶𝗼𝗻 𝗲𝘅𝗽𝗲𝗿𝘁. Our widely accepted shipping connections are made to easily interface with Odoo, simplifying everything from creating labels to tracking shipments—all from a single dashboard. We’re excited to introduce Chronopost Odoo Connectors your one stop solution for seamless global shipping management, now available on the Odoo App Store! At Vraja Technologies, we continue to be at the forefront of Odoo shipping integrations, ensuring your logistics run smoothly across countries. Users also search using these keywords Vraja Odoo Shipping Integration, Vraja Odoo shipping Connector, Vraja Shipping Integration, Vraja shipping Connector, Chronopost Odoo Shipping Integration, Chronopost Odoo shipping Connector, Chronopost Shipping Integration, Chronopost shipping Connector, Chronopost vraja technologies, Odoo Chronopost.

Chronopost Odoo Integration
Odoo Chronopost Shipping Module
Chronopost Shipping Odoo App
Odoo Chronopost Connector
Odoo Parcel Shipping Integration
Odoo Delivery Carrier Chronopost
Odoo Shipping Label Generator
Odoo Shipment Tracking Integration
Odoo eCommerce Shipping France
Odoo ERP Shipping Solution
Odoo Inventory Shipping Integration
Chronopost shipping integration with Odoo
Generate Chronopost labels in Odoo
Automate Chronopost shipping in Odoo ERP
Odoo Chronopost delivery integration
        vraja_shipping_solution France shipping integrations by Vraja''',
    'license': 'OPL-1',

    # Dependencies
    'depends': ['delivery','stock','stock_delivery'],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'data/pickup_point_service_demo.xml',
        'view/res_company.xml',
        'view/stock_picking.xml',
        'view/delivery_carrier.xml',
        'view/sale_order.xml'
    ],
    # Odoo Store Specific
    'images': ['static/description/cover.gif'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '199',
    'currency': 'EUR',

}
# version changelog
