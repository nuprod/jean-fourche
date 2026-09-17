from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_chronopost_relay_id = fields.Char(
        string='Shopify Chronopost Relay ID',
        help=(
            "Chronopost pickup point ID received from Shopify (order metafield "
            "'order.chronopost-relay-id'), set by the customer's checkout when the delivery "
            "method is a Chronopost pickup point."
        ),
    )

    def _resolve_shopify_chronopost_pickup_point(self):
        """
        Automatically set `chronopost_set_pickup_point_id` from the pickup point ID Shopify
        sent us, instead of requiring the "Get Locations" / "Set Location" manual steps.

        Shopify does not expose the pickup point's address, only its ID, so we still have to
        search Chronopost's pickup points for the delivery address (`get_locations`, already
        used by the manual flow) and match the result on `point_identifier`.
        """
        for order in self:
            relay_id = order.shopify_chronopost_relay_id
            if not relay_id or order.chronopost_set_pickup_point_id:
                continue

            if not order.carrier_id or not order.carrier_id.chronopost_product_code:
                order.message_post(body=_(
                    "Shopify a renvoyé un identifiant de point relais Chronopost (%s) pour cette "
                    "commande, mais le transporteur configuré n'est pas un transporteur Chronopost."
                ) % relay_id)
                continue

            try:
                order.get_locations()
            except Exception as ex:
                order.message_post(body=_(
                    "Échec de la recherche des points relais Chronopost pour l'identifiant "
                    "%(relay_id)s : %(error)s"
                ) % {'relay_id': relay_id, 'error': ex})
                continue

            point = order.chronopost_pickup_point_ids.filtered(
                lambda p: p.point_identifier == relay_id
            )
            if point:
                point[0].set_location()
            else:
                order.message_post(body=_(
                    "Le point relais Chronopost %s (reçu de Shopify) n'a pas été retrouvé parmi "
                    "les points relais disponibles pour l'adresse de livraison de cette commande."
                ) % relay_id)
