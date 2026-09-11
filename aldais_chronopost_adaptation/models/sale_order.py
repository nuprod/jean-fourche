# -*- coding: utf-8 -*-
"""
Recherche de points relais compatible 2Shop.

chronopost_shipping_integration (module Vraja) interroge exclusivement
recherchePointChronopostInterParService, avec un productCode vide. Les
échantillons Chronopost pour 2Shop (5X/6B) utilisent recherchePointChronopostInter
avec le vrai productCode. On bascule dessus uniquement quand le transporteur de
la commande est un des deux codes produit 2Shop concernés (5X, 6B) ; le flux
existant n'est pas modifié pour les autres transporteurs Chronopost.
"""
import xml.etree.ElementTree as etree

from odoo import models
from odoo.exceptions import ValidationError

from .delivery_carrier import CHRONOPOST_2SHOP_OUTBOUND_CODES


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def get_locations(self):
        for order in self:
            if order.carrier_id and order.carrier_id.chronopost_product_code in CHRONOPOST_2SHOP_OUTBOUND_CODES:
                order._chronopost_2shop_get_locations()
            else:
                super(SaleOrder, order).get_locations()

    def _chronopost_2shop_get_locations(self):
        self.ensure_one()
        order = self
        recipient_address = order.partner_shipping_id
        total_weight = sum((line.product_id.weight * line.product_uom_qty) for line in order.order_line) or 0.0

        root_node = etree.Element("soapenv:Envelope")
        root_node.attrib["xmlns:soapenv"] = "http://schemas.xmlsoap.org/soap/envelope/"
        root_node.attrib["xmlns:cxf"] = "http://cxf.rechercheBt.soap.chronopost.fr/"
        body_node = etree.SubElement(root_node, "soapenv:Body")
        search_node = etree.SubElement(body_node, "cxf:recherchePointChronopostInter")

        etree.SubElement(search_node, "accountNumber").text = order.carrier_id._chronopost_2shop_account_number() or ""
        etree.SubElement(search_node, "password").text = order.carrier_id._chronopost_2shop_password() or ""
        etree.SubElement(search_node, "address").text = recipient_address.street or ""
        etree.SubElement(search_node, "zipCode").text = recipient_address.zip or ""
        etree.SubElement(search_node, "city").text = recipient_address.city or ""
        etree.SubElement(search_node, "countryCode").text = recipient_address.country_id.code or ""
        etree.SubElement(search_node, "type").text = "P"
        etree.SubElement(search_node, "productCode").text = order.carrier_id.chronopost_product_code
        etree.SubElement(search_node, "service").text = "L"
        etree.SubElement(search_node, "weight").text = str(total_weight)
        etree.SubElement(search_node, "shippingDate").text = (order.date_order or order.create_date).strftime("%d/%m/%Y")
        etree.SubElement(search_node, "maxPointChronopost").text = "25"
        etree.SubElement(search_node, "maxDistanceSearch").text = "40"
        etree.SubElement(search_node, "holidayTolerant").text = "1"
        etree.SubElement(search_node, "language").text = "FR"

        header = {"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": ""}
        api_url = "{0}/recherchebt-ws-cxf/PointRelaisServiceWS".format(order.company_id.chronopost_api_url)
        response_status, response_data = order.carrier_id.chronopost_provider_create_shipment(
            "POST", api_url, etree.tostring(root_node), header
        )
        if not response_status:
            raise ValidationError(response_data)

        body = (response_data.get("Envelope") or {}).get("Body") or {}
        ret = (body.get("recherchePointChronopostInterResponse") or {}).get("return") or {}
        if ret.get("errorCode") not in (None, "0"):
            raise ValidationError(ret.get("errorMessage") or response_data)

        total_relay_points = ret.get("listePointRelais")
        pickup_point_obj = self.env["chronopost.pickup.point"]
        existing_records = pickup_point_obj.search([("sale_order_id", "=", order.id)])
        if existing_records:
            existing_records.sudo().unlink()
            self._cr.commit()
        if not total_relay_points:
            raise ValidationError("Please verify the address")

        relay_points = total_relay_points if isinstance(total_relay_points, list) else [total_relay_points]
        for relay_point in relay_points:
            country = self.env["res.country"].search([("code", "=", relay_point.get("codePays"))], limit=1)
            pickup_point_obj.create({
                "name": relay_point.get("nom"),
                "point_identifier": relay_point.get("identifiant"),
                "street": relay_point.get("adresse1"),
                "street2": relay_point.get("adresse2"),
                "zip": relay_point.get("codePostal"),
                "city": relay_point.get("localite"),
                "country_id": country.id,
                "sale_order_id": order.id,
            })
