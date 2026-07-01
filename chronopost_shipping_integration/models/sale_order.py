from odoo import fields, models
import logging
from odoo.exceptions import ValidationError
import xml.etree.ElementTree as etree

_logger = logging.getLogger("Chronopost")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chronopost_pickup_point_ids = fields.One2many(comodel_name='chronopost.pickup.point', inverse_name='sale_order_id',
                                                  help="List Of All The Pickup Point Based On The Selected Services",
                                                  copy=False,
                                                  string="Chronopost Pickup Points")
    chronopost_set_pickup_point_id = fields.Many2one(comodel_name='chronopost.pickup.point', copy=False,
                                                     help="Set Pickup Point As Location",
                                                     string="Locations")
    location_services_ids = fields.Many2many(comodel_name='pickup.point.service', copy=False,
                                             help="The locations will be filtered out according service provided",
                                             string="Location Services")

    def get_locations(self):
        order = self
        service_list = ';'.join(map(str, order.location_services_ids.mapped('pickup_point_service_id')))

        # Shipper and Recipient Address
        shipper_address = order.warehouse_id.partner_id
        recipient_address = order.partner_shipping_id
        total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0

        root_node = etree.Element("Envelope")
        root_node.attrib['xmlns'] = "http://schemas.xmlsoap.org/soap/envelope/"

        body_node = etree.SubElement(root_node, "Body")

        recherche_point_node = etree.SubElement(body_node, "recherchePointChronopostInterParService")
        recherche_point_node.attrib['xmlns'] = "http://cxf.rechercheBt.soap.chronopost.fr/"

        etree.SubElement(recherche_point_node,
                         "accountNumber", xmlns="").text = self.company_id and self.company_id.chronopost_account_number or ""
        etree.SubElement(recherche_point_node, "password", xmlns="").text = self.company_id and self.company_id.chronopost_password or ""
        etree.SubElement(recherche_point_node, "address", xmlns="").text = recipient_address.street
        etree.SubElement(recherche_point_node, "zipCode", xmlns="").text = recipient_address.zip
        etree.SubElement(recherche_point_node, "city", xmlns="").text = recipient_address.city
        etree.SubElement(recherche_point_node, "countryCode", xmlns="").text = recipient_address.country_code
        etree.SubElement(recherche_point_node, "type", xmlns="").text = "P"
        etree.SubElement(recherche_point_node, "productCode",
                         xmlns="").text = ''  # order.carrier_id.chronopost_product_code
        etree.SubElement(recherche_point_node, "service", xmlns="").text = "L"
        etree.SubElement(recherche_point_node, "weight", xmlns="").text = str(total_weight)
        etree.SubElement(recherche_point_node, "shippingDate", xmlns="").text = order.date_order.strftime("%d/%m/%Y")
        etree.SubElement(recherche_point_node, "maxPointChronopost", xmlns="").text = '25'
        etree.SubElement(recherche_point_node, "maxDistanceSearch", xmlns="").text = '40'
        etree.SubElement(recherche_point_node, "holidayTolerant", xmlns="").text = '1'
        etree.SubElement(recherche_point_node, "serviceList", xmlns="").text = service_list
        etree.SubElement(recherche_point_node, "language", xmlns="").text = self.company_id and self.company_id.country_id and self.company_id.country_id.code or ""
        etree.SubElement(recherche_point_node, "version", xmlns="").text = '2.0'

        try:
            header = {'Content-Type': 'text/xml;charset=UTF-8',
                      'SOAPAction': ""}
            api_url = "{0}/recherchebt-ws-cxf/PointRelaisServiceWS".format(self.company_id.chronopost_api_url)
            request_data = etree.tostring(root_node)
            request_type = "POST"
            response_status, response_data = order.carrier_id.chronopost_provider_create_shipment(
                request_type, api_url,
                request_data,
                header)
            if response_status and response_data:
                total_relay_points = response_data.get('Envelope') and response_data.get('Envelope').get(
                    'Body') and response_data.get('Envelope').get('Body').get(
                    'recherchePointChronopostInterParServiceResponse') and response_data.get('Envelope').get(
                    'Body').get('recherchePointChronopostInterParServiceResponse').get(
                    'return') and response_data.get('Envelope').get('Body').get(
                    'recherchePointChronopostInterParServiceResponse').get('return').get('listePointRelais')
                chronopost_pickup_point_obj = self.env['chronopost.pickup.point']
                existing_records = chronopost_pickup_point_obj.search(
                    [('sale_order_id', '=', order and order.id)])
                if existing_records:
                    existing_records.sudo().unlink()
                    self._cr.commit()
                if total_relay_points:
                    for relay_point_list in total_relay_points:
                        country_code = self.env['res.country'].search([('code', '=', relay_point_list.get('codePays'))])
                        vals = {
                            'name': relay_point_list.get('nom'),
                            'point_identifier': relay_point_list.get('identifiant'),
                            'street': relay_point_list.get('adresse1'),
                            'street2': relay_point_list.get('adresse2'),
                            'zip': relay_point_list.get('codePostal'),
                            'city': relay_point_list.get('localite'),
                            'country_id': country_code.id,
                            'sale_order_id': order.id
                        }
                        chronopost_pickup_point_obj.create(vals)
                else:
                    raise ValidationError("Please verify the address")
        except Exception as e:
            raise ValidationError(e)
