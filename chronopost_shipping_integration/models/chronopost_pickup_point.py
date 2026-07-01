from odoo import fields, models


class ChronopostPickupPoint(models.Model):
    _name = 'chronopost.pickup.point'
    description = "Chronopost Pickup Point Location Details"

    name = fields.Char(string="Point Name")
    point_identifier = fields.Char(string="Point ID")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    zip = fields.Char(string="Zip")
    city = fields.Char(string="City")
    country_id = fields.Many2one(comodel_name='res.country')
    sale_order_id = fields.Many2one("sale.order", string="Sales Order")

    def set_location(self):
        self.sale_order_id.chronopost_set_pickup_point_id = self.id


class PickupPointService(models.Model):
    _name = 'pickup.point.service'
    _rec_name = 'pickup_point_service_name'

    pickup_point_service_id = fields.Integer(string="Pickup Point Service ID")
    pickup_point_service_name = fields.Char(string="Pickup Point Service Name")

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.pickup_point_service_id} - {rec.pickup_point_service_name}'
