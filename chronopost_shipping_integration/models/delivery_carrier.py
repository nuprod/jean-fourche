import logging
import requests
import binascii
import xml.etree.ElementTree as etree
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.chronopost_shipping_integration.models.response import Response

_logger = logging.getLogger("Chronopost")


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("chronopost_provider", "chronopost")],
                                     ondelete={'chronopost_provider': 'set default'})
    chronopost_provider_package_id = fields.Many2one('stock.package.type', string="Package Info",
                                                     help="Default Package")
    chronopost_shipper_civility = fields.Selection([("E", "Madame"), ("L", "Mademoiselle"), ("M", "Monsieur")],
                                                   string="Shipper Civility")

    chronopost_package_type = fields.Selection([("DOC", "Document"), ("MAR", "Marchandise")],
                                               string="Package type")
    chronopost_service = fields.Selection(
        [("0", "Normal"), ("1", "Delivery Monday (only for national product codes)"),
         ("6", "Saturday delivery (for national product codes only)")],
        string="Service")

    chronopost_label_mode = fields.Selection(
        [("PDF", "PDF"), ("SPD", "SPD"), ("THE", "THE"), ("SER", "SER"), ("XML", "XML")],
        string="Label Type")
    chronopost_with_reservation = fields.Selection(
        [("0", "Without reservation"), ("1", "With reservation (returns only the reservation number)"), (
            "2",
            "With reservation (returns the reservation number and the first LT format specified in the mode)")],
        string="With Reservation")

    chronopost_mode_retour = fields.Selection(
        [("1", "The label will be sent by email to the sender's email address"),
         ("2", "The label will not be emailed to the sender's email address"),
         ("3", "The label can be printed on a machine at the post office")],
        string="Return Mode")
    chronopost_pre_alert = fields.Selection(
        [("0", "No pre-alert"),
         ("22", "Recipient email pre-alert")],
        string="Type of pre-alert (MAS)")

    chronopost_product_code = fields.Selection([('0', 'Chrono Retrait Bureau'),
                                                ('01', 'Chrono 13'),
                                                ('2', 'Chrono 10'),
                                                ('9', 'Chrono REP'),
                                                ('16', 'Chrono 18'),
                                                ('17', 'Chrono Express'),
                                                ('20', 'Chrono Agenda'),
                                                ('37', 'Chrono Premium'),
                                                ('44', 'Chrono Classic'),
                                                ('49', 'Chrono Relais Europe'),
                                                ('58', 'Chrono 13 BAL (instance relais et Poste)'),
                                                ('75', 'Chrono 8'),
                                                ('76', 'Chrono 9'),
                                                ('77', 'Chrono 12'),
                                                ('78', 'Chrono Temp° 13'),
                                                ('80', 'Chrono 9 relais'),
                                                ('86', 'Chrono Relais'),
                                                ('93', 'Chrono 13 Instance Poste'),
                                                ('1F', 'Chrono 13 (remise pas de porte possible)'),
                                                ('1G', 'Chrono 13 (remise pas de porte possible)'),
                                                ('1K', 'Chrono Temp° 10'),
                                                ('1M', 'Chrono Marchandises Dangereuses 13'),
                                                ('1N', 'Chrono Marchandises Dangereuses 18'),
                                                ('1O', 'Chrono Swap 13'),
                                                ('1P', 'Chrono Swap 18'),
                                                ('1S', 'Chrono 13 Instance Agence'),
                                                ('1T', 'Chrono 13 Instance Relais'),
                                                ('1U', 'Chrono 10 sans instance Poste'),
                                                ('1V', 'Chrono 18 Instance Agence'),
                                                ('1Y', 'Chrono 13 Livraison/Collecte'),
                                                ('2A', 'Chrono 8 medical'),
                                                ('2B', 'Chrono 9 medical'),
                                                ('2E', 'Chrono Fresh Rendez-Vous'),
                                                ('2F', 'Chrono Freeze Rendez-Vous'),
                                                ('2L', 'Chrono 18 (livraison en boîte aux lettres)'),
                                                ('2M', 'Chrono 18 (livraison en boîte aux lettres, instance mixte)'),
                                                ('2O', 'Chrono Rendez-Vous'),
                                                ('2P', 'Chrono Fresh same day'),
                                                ('2Q', 'Chrono Freeze same day'),
                                                ('2R', 'Chrono Fresh 13'),
                                                ('2S', 'Chrono Freeze 13'),
                                                ('3J', 'Chrono Zengo 13'),
                                                ('3K', 'Chrono Zengo Relais 13'),
                                                ('3S', 'Chrono Fret Dom'),
                                                ('3T', 'Chrono Retour Europe'),
                                                ('3X', 'Chrono Fresh 10'),
                                                ('3Y', 'Chrono Freeze 10'),
                                                ('3Z', 'Chrono 18 (instance relais)'),
                                                ('4I', 'Chrono Same Day'),
                                                ('4P', 'Chrono Relais Dom'),
                                                ('4Q', 'Chrono Direct'),
                                                ('4R', 'Chrono Reverse 9'),
                                                ('4S', 'Chrono Reverse 10'),
                                                ('4T', 'Chrono Reverse 13'),
                                                ('4U', 'Chrono Reverse 18'),
                                                ('4V', 'Chrono Fresh 12'),
                                                ('4W', 'Chrono Freeze 12'),
                                                ('4X', 'Chrono Fresh Classic'),
                                                ('8A', 'Chrono Medical 10'),
                                                ('8B', 'Chrono Medical 13'),
                                                ('8C', 'Chrono Medical 18'),
                                                ('8D', 'Chrono Medical 10 thermosensible'),
                                                ('8E', 'Chrono Medical 13 thermosensible'),
                                                ('8F', 'Chrono Medical 18 thermosensible'),
                                                ('8G', 'Chrono Medical Marchandises Dangereuses 13'),
                                                ('8H', 'Chrono Medical Marchandises Dangereuses 18'),
                                                ('8I', 'Chrono Medical Marchandises Dangereuses 13 thermosensible'),
                                                ('8J', 'Chrono Medical Marchandises Dangereuses 18 thermosensible')],
                                               string="Product Code")

    def check_address_details(self, address_id, required_fields):
        """
            check the address of Shipper and Recipient
            param : address_id: res.partner, required_fields: ['zip', 'city', 'country_id', 'street']
            return: missing address message
        """

        res = [field for field in required_fields if not address_id[field]]
        if res:
            return "Missing Values For Address :\n %s" % ", ".join(res).replace("_id", "")

    def chronopost_provider_rate_shipment(self, order):
        """
           This method is used for get rate of shipment
           param : order : sale.order
           return: 'success': False : 'error message' : True
           return: 'success': True : 'error_message': False
        """
        # Shipper and Recipient Address
        shipper_address_id = order.warehouse_id.partner_id
        recipient_address_id = order.partner_shipping_id

        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['zip', 'city', 'country_id', 'street'])
        total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0

        product_weight = (order.order_line.filtered(
            lambda x: not x.is_delivery and x.product_id.type == 'product' and x.product_id.weight <= 0))
        product_name = ", ".join(product_weight.mapped('product_id').mapped('name'))

        if shipper_address_error or recipient_address_error or product_name:
            return {'success': False, 'price': 0.0,
                    'error_message': "%s %s  %s " % (
                        "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                        "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                        "product weight is not available : %s" % (product_name) if product_name else ""
                    ),
                    'warning_message': False}

        root_node_envelope = etree.Element('Envelope')
        root_node_envelope.attrib['xmlns'] = 'http://schemas.xmlsoap.org/soap/envelope/'
        root_body = etree.SubElement(root_node_envelope, 'Body')
        root_quickcost = etree.SubElement(root_body, 'quickCost')
        root_quickcost.attrib['xmlns'] = 'http://cxf.quickcost.soap.chronopost.fr/'
        etree.SubElement(root_quickcost, 'accountNumber', xmlns="").text = self.company_id.chronopost_account_number
        etree.SubElement(root_quickcost, 'password', xmlns="").text = self.company_id.chronopost_password
        etree.SubElement(root_quickcost, 'depCode', xmlns="").text = shipper_address_id.zip
        etree.SubElement(root_quickcost, 'arrCode', xmlns="").text = recipient_address_id.zip
        etree.SubElement(root_quickcost, 'weight', xmlns="").text = str(total_weight)
        etree.SubElement(root_quickcost, 'productCode', xmlns="").text = self.chronopost_product_code
        etree.SubElement(root_quickcost, 'type', xmlns="").text = "D" if self.chronopost_package_type == "DOC" else "M"

        try:
            header = {'Content-Type': 'application/xml'}
            api_url = "{0}/quickcost-cxf/QuickcostServiceWS".format(self.company_id.chronopost_api_url)
            request_data = etree.tostring(root_node_envelope)
            request_type = "POST"
            response_status, response_data = self.chronopost_provider_create_shipment(request_type, api_url,
                                                                                      request_data,
                                                                                      header)

            if response_status:
                chronopost_rate = response_data.get('Envelope') and response_data.get('Envelope').get(
                    'Body') and response_data.get('Envelope').get('Body').get(
                    'quickCostResponse') and response_data.get('Envelope').get('Body').get('quickCostResponse').get(
                    'return') and response_data.get('Envelope').get('Body').get('quickCostResponse').get('return').get(
                    'amount')
                error_message = response_data.get('Envelope').get('Body').get('quickCostResponse').get(
                    'return') and response_data.get('Envelope').get('Body').get('quickCostResponse').get(
                    'return').get(
                    'errorMessage')
                if chronopost_rate:
                    return {'success': True, 'price': chronopost_rate,
                            'error_message': False, 'warning_message': error_message}
                else:
                    return {'success': False, 'price': 0.0,
                            'error_message': False, 'warning_message': error_message}
            else:
                return {'success': False, 'price': 0.0,
                        'error_message': response_data, 'warning_message': False}
        except Exception as e:
            return {'success': False, 'price': 0.0,
                    'error_message': e, 'warning_message': False}

    def chronopost_provider_create_shipment(self, request_type, api_url, request_data, header):
        _logger.info("Shipment Request API URL:::: %s" % api_url)
        _logger.info("Shipment Request Data:::: %s" % request_data)
        response_data = requests.request(method=request_type, url=api_url, headers=header, data=request_data)
        if response_data.status_code in [200, 201]:
            response_data = Response(response_data)
            response_data = response_data.dict()
            _logger.info(">>> Response Data {}".format(response_data))
            return True, response_data
        else:
            return False, response_data.text

    def chronopost_provider_send_shipping(self, picking):
        shipper_address_id = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
        recipient_address_id = picking.sale_id.chronopost_set_pickup_point_id if picking.sale_id and picking.sale_id.chronopost_set_pickup_point_id else picking.partner_id
        company_id = self.company_id
        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['zip', 'city', 'country_id', 'street'])
        if shipper_address_error or recipient_address_error or not picking.shipping_weight:
            raise ValidationError("%s %s  %s " % (
                "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                "Shipping weight is missing!" if not picking.shipping_weight else ""
            ))

        sender_zip = shipper_address_id.zip or ""
        sender_city = shipper_address_id.city or ""
        sender_country_code = shipper_address_id.country_id and shipper_address_id.country_id.code or ""
        sender_street = shipper_address_id.street or ""
        sender_street2 = shipper_address_id.street2 or ""
        sender_phone = shipper_address_id.phone or ""
        sender_email = shipper_address_id.email or ""

        receiver_zip = recipient_address_id.zip or ""
        receiver_city = recipient_address_id.city or ""
        receiver_country_code = recipient_address_id.country_id and recipient_address_id.country_id.code or ""
        receiver_street = recipient_address_id.street or ""
        receiver_street2 = recipient_address_id.street2 or ""
        receiver_phone = picking.partner_id.phone or ""
        receiver_email = picking.partner_id.email or ""

        # prepare root tag
        root_node_envelope = etree.Element('soapenv:Envelope')
        root_node_envelope.attrib['xmlns:soapenv'] = 'http://schemas.xmlsoap.org/soap/envelope/'
        root_node_envelope.attrib['xmlns:cxf'] = 'http://cxf.shipping.soap.chronopost.fr/'

        # prepare header
        etree.SubElement(root_node_envelope, 'soapenv:Header')
        root_body = etree.SubElement(root_node_envelope, 'soapenv:Body')
        root_shipping_multiParcel = etree.SubElement(root_body, 'cxf:shippingMultiParcel')
        auth_header_value = etree.SubElement(root_shipping_multiParcel, 'headerValue')
        etree.SubElement(auth_header_value, 'accountNumber').text = company_id.chronopost_account_number
        etree.SubElement(auth_header_value, 'idEmit').text = "CHRFR"
        etree.SubElement(auth_header_value, 'identWebPro').text = ""
        etree.SubElement(auth_header_value, 'subAccount').text = "0"

        # shipper Value
        shipperValue = etree.SubElement(root_shipping_multiParcel, 'shipperValue')
        etree.SubElement(shipperValue, 'shipperName').text = shipper_address_id.name or ""
        etree.SubElement(shipperValue, 'shipperCivility').text = self.chronopost_shipper_civility
        etree.SubElement(shipperValue, 'shipperAdress1').text = sender_street
        etree.SubElement(shipperValue, 'shipperAdress2').text = sender_street2
        etree.SubElement(shipperValue, 'shipperZipCode').text = sender_zip
        etree.SubElement(shipperValue, 'shipperCity').text = sender_city
        etree.SubElement(shipperValue, 'shipperCountry').text = sender_country_code
        etree.SubElement(shipperValue, 'shipperCountryName').text = shipper_address_id.country_id.name or ""
        etree.SubElement(shipperValue, 'shipperEmail').text = sender_email
        etree.SubElement(shipperValue, 'shipperPhone').text = sender_phone
        etree.SubElement(shipperValue, 'shipperMobilePhone').text = shipper_address_id.mobile or ""

        # customer value
        customerValue = etree.SubElement(root_shipping_multiParcel, 'customerValue')


        etree.SubElement(customerValue, 'customerName').text = recipient_address_id.name or ""
        etree.SubElement(customerValue, 'customerName2').text = recipient_address_id.name or ""
        etree.SubElement(customerValue, 'customerCivility').text = self.chronopost_shipper_civility
        etree.SubElement(customerValue, 'customerAdress1').text = receiver_street
        etree.SubElement(customerValue, 'customerAdress2').text = receiver_street2
        etree.SubElement(customerValue, 'customerZipCode').text = receiver_zip
        etree.SubElement(customerValue, 'customerCity').text = receiver_city
        etree.SubElement(customerValue, 'customerCountry').text = receiver_country_code
        etree.SubElement(customerValue,
                         'customerCountryName').text = recipient_address_id.country_id.name or ""
        etree.SubElement(customerValue, 'customerContactName').text = recipient_address_id.name or ""
        etree.SubElement(customerValue, 'customerEmail').text = receiver_email
        etree.SubElement(customerValue, 'customerPhone').text = receiver_phone
        etree.SubElement(customerValue, 'customerMobilePhone').text = picking.partner_id.mobile or ""
        etree.SubElement(customerValue, 'printAsSender').text = ""

        # recipient Value
        recipientValue = etree.SubElement(root_shipping_multiParcel, 'recipientValue')
        etree.SubElement(recipientValue, 'recipientName').text = recipient_address_id.name or ""
        etree.SubElement(recipientValue, 'recipientAdress1').text = receiver_street
        etree.SubElement(recipientValue, 'recipientAdress2').text = receiver_street2
        etree.SubElement(recipientValue, 'recipientZipCode').text = receiver_zip
        etree.SubElement(recipientValue, 'recipientCity').text = receiver_city
        etree.SubElement(recipientValue, 'recipientCountry').text = receiver_country_code
        etree.SubElement(recipientValue, 'recipientCountryName').text = recipient_address_id.country_id.name or ""
        etree.SubElement(recipientValue, 'recipientEmail').text = receiver_email
        etree.SubElement(recipientValue, 'recipientPhone').text = receiver_phone
        etree.SubElement(recipientValue, 'recipientMobilePhone').text = picking.partner_id.mobile or ""
        etree.SubElement(recipientValue, 'recipientPreAlert').text = self.chronopost_pre_alert or ""

        # refValue
        refValue = etree.SubElement(root_shipping_multiParcel, 'refValue')
        etree.SubElement(refValue, 'customerSkybillNumber').text = ""
        etree.SubElement(refValue, 'recipientRef').text = picking.partner_id.ref or ""

        # skybillValue
        skybillValue = etree.SubElement(root_shipping_multiParcel, 'skybillValue')
        etree.SubElement(skybillValue, 'customsCurrency').text = company_id.currency_id.name
        etree.SubElement(skybillValue, 'customsValue').text = "0"  # Customs declared value
        etree.SubElement(skybillValue, 'evtCode').text = "DC"  # fix
        etree.SubElement(skybillValue, 'objectType').text = self.chronopost_package_type
        etree.SubElement(skybillValue, 'productCode').text = self.chronopost_product_code
        etree.SubElement(skybillValue, 'service').text = self.chronopost_service
        etree.SubElement(skybillValue, 'shipDate').text = picking.scheduled_date.strftime("%Y-%m-%d")
        etree.SubElement(skybillValue, 'weight').text = str(picking.shipping_weight)
        etree.SubElement(skybillValue, 'weightUnit').text = "KGM"
        etree.SubElement(skybillValue,
                         'height').text = str(self.chronopost_provider_package_id.height) or "0"
        etree.SubElement(skybillValue,
                         'length').text = str(self.chronopost_provider_package_id.packaging_length) or "0"
        etree.SubElement(skybillValue,
                         'width').text = str(self.chronopost_provider_package_id.width) or "0"

        # skybillParamsValue
        skybillParamsValue = etree.SubElement(root_shipping_multiParcel, 'skybillParamsValue')
        etree.SubElement(skybillParamsValue, 'mode').text = self.chronopost_label_mode
        etree.SubElement(skybillParamsValue,
                         'withReservation').text = self.chronopost_with_reservation  # Does the LT must be saved to be recovered later or should she be sent upon return from ws? Parameters do not exist in the case of services shipping and shippingWithReservationAndESDWithRefClient 0: Without reservation 1: With reservation (returns only on booking number) 2: With reservation (returns the number of reservation and the first format of the LT specified in mode)

        etree.SubElement(root_shipping_multiParcel, 'password').text = company_id.chronopost_password
        etree.SubElement(root_shipping_multiParcel,
                         'modeRetour').text = self.chronopost_mode_retour  # Indicates whether the label should be sent by email 1: the label will be returned by email to the sender's email address 2: the label will not be returned by email to the email address from the sender
        etree.SubElement(root_shipping_multiParcel, 'numberOfParcel').text = str(picking.chronopost_number_of_parcel)
        etree.SubElement(root_shipping_multiParcel, 'multiParcel').text = "Y"

        try:
            header = {'Content-Type': 'application/xml'}
            api_url = "{}/shipping-cxf/ShippingServiceWS".format(company_id.chronopost_api_url)
            request_data = etree.tostring(root_node_envelope)
            request_type = "POST"
            response_status, response_data = self.chronopost_provider_create_shipment(request_type, api_url,
                                                                                      request_data,
                                                                                      header)
            tracking_skybill_number = []
            if response_status and response_data.get('Envelope') and response_data.get('Envelope').get(
                    'Body') and response_data.get('Envelope').get('Body').get(
                'shippingMultiParcelResponse') and response_data.get('Envelope').get('Body').get(
                'shippingMultiParcelResponse').get('return').get(
                'resultMultiParcelValue'):

                if self.chronopost_with_reservation == "1":
                    reservation_number = response_data.get('Envelope').get('Body').get(
                        'shippingMultiParcelResponse').get('return').get('reservationNumber')
                    skybill_numbers = response_data.get('Envelope').get('Body').get(
                        'shippingMultiParcelResponse').get('return').get(
                        'resultMultiParcelValue')
                    for skybill_number in skybill_numbers:
                        tracking_skybill_number.append(skybill_number.get('skybillNumber'))
                    logmessage = (_(" Reservation Number : %s") % (reservation_number))
                    picking.message_post(body=logmessage)
                    shipping_data = {'exact_price': 0.0, 'tracking_number': ",".join(tracking_skybill_number)}
                    shipping_data = [shipping_data]
                    return shipping_data

                multi_packages = response_data.get('Envelope').get('Body').get('shippingMultiParcelResponse').get(
                    'return').get('resultMultiParcelValue')
                if picking.chronopost_number_of_parcel > 1:
                    for index, package in enumerate(multi_packages, start=1):
                        skybill_number = package.get('skybillNumber')
                        label_data = package.get('pdfEtiquette')
                        binary_data = binascii.a2b_base64(str(label_data))
                        tracking_skybill_number.append(skybill_number)
                        picking.message_post(attachments=[
                            ('LabelShipping-chronopost-%s.%s' % (index, self.chronopost_label_mode), binary_data)])
                else:
                    skybill_number = response_data.get('Envelope').get('Body').get('shippingMultiParcelResponse').get(
                        'return').get('resultMultiParcelValue').get('skybillNumber')
                    label_data = response_data.get('Envelope').get('Body').get('shippingMultiParcelResponse').get(
                        'return').get('resultMultiParcelValue').get('pdfEtiquette')
                    binary_data = binascii.a2b_base64(str(label_data))
                    tracking_skybill_number.append(skybill_number)
                    picking.message_post(
                        attachments=[('LabelShipping-chronopost-1.%s' % (self.chronopost_label_mode), binary_data)])
                shipping_data = {'exact_price': 0.0, 'tracking_number': ",".join(tracking_skybill_number)}
                shipping_data = [shipping_data]
                return shipping_data
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def chronopost_provider_cancel_shipment(self, picking):

        root_node_envelope = etree.Element('soapenv:Envelope')
        root_node_envelope.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
        root_node_envelope.attrib['xmlns:cxf'] = "http://cxf.tracking.soap.chronopost.fr/"
        etree.SubElement(root_node_envelope, 'soapenv:Header')
        root_body = etree.SubElement(root_node_envelope, 'soapenv:Body')
        root_cancelskybill = etree.SubElement(root_body, 'cxf:cancelSkybill')
        etree.SubElement(root_cancelskybill, 'accountNumber').text = self.company_id.chronopost_account_number
        etree.SubElement(root_cancelskybill, 'password').text = self.company_id.chronopost_password
        etree.SubElement(root_cancelskybill, 'language').text = "fr_FR"
        etree.SubElement(root_cancelskybill, 'skybillNumber').text = picking.carrier_tracking_ref

        try:
            header = {'Content-Type': 'application/xml'}
            api_url = "{}/tracking-cxf/TrackingServiceWS".format(self.company_id.chronopost_api_url)
            request_data = etree.tostring(root_node_envelope)
            request_type = "POST"
            response_status, response_data = self.chronopost_provider_create_shipment(request_type, api_url,
                                                                                      request_data,
                                                                                      header)

            if response_status and response_data.get('Envelope') and response_data.get('Envelope').get(
                    'Body') and response_data.get('Envelope').get('Body').get(
                'cancelSkybillResponse') and response_data.get('Envelope').get('Body').get('cancelSkybillResponse').get(
                'return'):
                if response_data.get('Envelope').get('Body').get('cancelSkybillResponse').get('return').get(
                        'errorCode') == '0':
                    _logger.info("successfully delete the shipment")
                else:
                    error_message = response_data.get('Envelope').get('Body').get('cancelSkybillResponse').get(
                        'return').get('errorMessage')
                    raise ValidationError(error_message)
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def chronopost_provider_get_tracking_link(self, picking):
        return "https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={0}".format(
            picking.carrier_tracking_ref)
