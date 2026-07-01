from odoo import models, fields


class PackageDetails(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[("chronopost_provider", "chronopost")],
                                            ondelete={'chronopost_provider': 'set default'})
