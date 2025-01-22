# Copyright 2023 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).


from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Deactivate the server action 'Create Vendor Bills' once this app is installed"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    vendor_bill_server_action = env.ref("purchase.action_purchase_batch_bills")
    if vendor_bill_server_action:
        vendor_bill_server_action.write({"binding_model_id": ""})
