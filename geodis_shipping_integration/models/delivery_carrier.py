# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError
import requests
import hashlib
import time
import json
import logging
import binascii
_logger = logging.getLogger("GEODIS")
from collections import OrderedDict

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("geodis", "GEODIS")],
                                     ondelete={'geodis': 'set default'})

    geodis_package_id = fields.Many2one('stock.package.type', string='Default Package')

    suppression_validation = fields.Boolean(string='Delete The Shipment In Case Of Validation Failure')
    format_etiquette = fields.Selection([('1', '1-135'),
                                         ('2', '2-150')], string="Format Label")
    product_code = fields.Char(string="Product Code")
    option_livraison = fields.Selection([('RDW', 'Rendez-vous Web'),
                                        ('RDT', 'Rendez-vous téléphonique'),
                                        ('BRT', 'Retrait en agence GEODIS'),
                                        ('DSL', 'Date souhaitée de Livraison'),
                                        ('SAM', 'Livraison un Samedi Matin')], string="Delivery Option") 

    def geodis_rate_shipment(self, order):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def geodis_prepare_request_date(self, pickings):
        """
        prepare data dictionary to send geodis
        :param pickings
        :return data dict
        """
        sender_id = pickings.picking_type_id and pickings.picking_type_id.warehouse_id and pickings.picking_type_id.warehouse_id.partner_id
        receiver_id = pickings.partner_id

        # check sender Address
        if not sender_id.zip or not sender_id.city or not sender_id.country_id:
            raise ValidationError("Please Define Proper Sender Address!")

        # check Receiver Address
        if not receiver_id.zip or not receiver_id.city or not receiver_id.country_id:
            raise ValidationError("Please Define Proper Recipient Address!")
        parcel_data = []
        total_bulk_weight = pickings.weight_bulk
        for package_id in pickings.package_ids:
            parcel_data.append({
                "palette": "False",
                "paletteConsignee": "False",
                "quantite": 1,
                "poids": package_id.shipping_weight,
                "volume": 0.1,
                "longueurUnitaire": package_id.package_type_id and package_id.package_type_id.packaging_length or 0,
                "largeurUnitaire": package_id.package_type_id.width or 0,
                "hauteurUnitaire": package_id.package_type_id.height or 0,
                "referenceColis": ""
            })
        if total_bulk_weight:
            for number in range(pickings.number_of_label):
                parcel_data.append({
                    "palette": "False",
                    "paletteConsignee": "False",
                    "quantite": 1,
                    "poids": round(total_bulk_weight / float(pickings.number_of_label),2),
                    "volume": 0.1,
                    "longueurUnitaire": int(self.geodis_package_id.packaging_length or 0),
                    "largeurUnitaire": int(self.geodis_package_id.width),
                    "hauteurUnitaire": int(self.geodis_package_id.height or 0),
                    "referenceColis": ""
                })

        data = {
            "impressionEtiquette": "False",
            "typeImpressionEtiquette": "P",
            "formatEtiquette": str(self.format_etiquette),
            "validationEnvoi": "false",
            "suppressionSiEchecValidation": "false",#self.suppression_validation,
            "impressionBordereau": "false",
            "impressionRecapitulatif": "false",
            "listEnvois": [
                {
                    "noRecepisse": "",#pickings.name,  # Receipt number
                    "noSuivi": "",
                    "codeSa": self.company_id.agency_code,#"020017",  # Ordering agency code
                    "codeClient": self.company_id.customer_account,#"601911",  # Customer account
                    "codeProduit": self.product_code,#"MES",  # Product code of the service
                    "reference1": pickings and pickings.name or '',
                    "expediteur": {  # sender
                        "nom": sender_id and sender_id.name or '',
                        "adresse1": sender_id and sender_id.street or '',
                        "adresse2": "",
                        "codePostal": sender_id.zip or '',
                        "ville": sender_id and sender_id.city or '',
                        "codePays": sender_id and sender_id.country_id and sender_id.country_id.code,
                        "nomContact": sender_id.name,  # contact name
                        "email": sender_id.email or " ",
                        "telFixe": sender_id.phone or " ",
                        "telMobile": sender_id.mobile or " ",

                    },
                    "dateDepartEnlevement": pickings.scheduled_date.strftime("%Y-%m-%d"),  # date

                    "destinataire": {
                        "nom": receiver_id.name or "",
                        "adresse1": receiver_id.street or "",
                        "adresse2": receiver_id.street2 or " ",
                        "codePostal": receiver_id.zip or "",
                        "ville": receiver_id.city or "",
                        "codePays": receiver_id and receiver_id.country_id and receiver_id.country_id.code,
                        "nomContact": receiver_id.name or "",
                        "email": receiver_id.email or ' ',
                        "telFixe": receiver_id.phone or " ",
                        "telMobile": receiver_id.mobile or ' '
                    },
                    "listUmgs":parcel_data,
                    "poidsTotal":pickings.shipping_weight or 0,
                    # "volumeTotal":,
                    "optionLivraison": str(self.option_livraison),
                    "emailNotificationDestinataire": receiver_id.email or '',
                    "smsNotificationDestinataire": receiver_id.mobile or ''
                }
             ]
        }
        json_data = json.dumps(data)
        _logger.info(">>>>>Shipping Request Data::::%s" % json_data)
        return json_data

    def get_hash(self, api_key, id, timestamp, lang, service, json_data):
        return hashlib.sha256(
            ";".join([
                api_key, id, timestamp, lang, service,
                json_data
            ]).encode("utf-8")
        ).hexdigest()

    def get_token(self, id, timestamp, lang, hash):
        params = [id, timestamp, lang, hash]
        return ';'.join(params)

    def validate_shipping_request(self, pickings, tracking_number):
        payload = {
            "impressionBordereau": "True",
            "listNosSuivis": tracking_number  # ["1G0N2M7LX9D2"]
        }
        data = json.dumps(payload)
        _logger.info(">>>>>>Validate shipping request data::::%s" % data)
        return data

    def geodis_send_shipping(self, pickings):
        response = []
        try:
            request_data = self.geodis_prepare_request_date(pickings)
            api_key = self.company_id.geodis_api_key  # "12345678"
            timestamp = "%d" % (time.time() * 1000)
            lang = "en"
            service = "api/wsclient/enregistrement-envois"
            url = "%sapi/wsclient/enregistrement-envois" % self.company_id.geodis_api_url
            id = self.company_id.geodis_id  # "DEMO"
            hash = self.get_hash(api_key, id, timestamp, lang, service, request_data)
            token = self.get_token(id, timestamp, lang, hash)
            headers = {'X-GEODIS-Service': token}
            response_data = requests.request("POST", url=url, headers=headers,
                                             data=request_data)
            _logger.info(">>>>>Shipping Response::::%s" % response_data.text)
            if response_data.status_code in [200, 201]:
                response_body = response_data.json()  # self.response()#
                _logger.info("Json Shipping Response::::%s" % response_body)
                if response_body.get('ok') == True:
                    tracking_number = []
                    for data in response_body.get('contenu') and response_body.get('contenu').get('listRetoursEnvois'):
                        if data.get('msgErreurEnregistrement'):
                            raise ValidationError(data.get('msgErreurEnregistrement').get('texte'))
                        tracking_number.append(data.get('noSuivi'))
                        base64_data = data.get('docEtiquette') and data.get('docEtiquette').get('contenu')
                        binary_data = binascii.a2b_base64(
                            str(base64_data))
                        pickings.message_post(attachments=[("%s.pdf" % (pickings.name), binary_data)])
                    pickings.carrier_tracking_ref = ','.join(tracking_number)

                    # Here Code Start For Validate Shipping Request

                    request_data = self.validate_shipping_request(pickings, tracking_number)
                    service = "api/wsclient/validation-envois"
                    validate_url = "%sapi/wsclient/validation-envois" % self.company_id.geodis_api_url
                    hash = self.get_hash(api_key, id, timestamp, lang, service, request_data)
                    token = self.get_token(id, timestamp, lang, hash)
                    headers = {'X-GEODIS-Service': token}
                    response_data = requests.request("POST", url=validate_url, headers=headers,
                                                     data=request_data)
                    _logger.info(">>>>>Validate Shipping Response:::: %s" % response_data.content)
                    shipping_data = {'exact_price': 0.0, 'tracking_number': pickings.carrier_tracking_ref}
                    response += [shipping_data]
                    return response

                else:
                    raise ValidationError(response_body)
            else:
                raise ValidationError(response_data.content)
        except Exception as e:
            raise ValidationError(_("\n Response Data : %s") % (e))

    def geodis_cancel_shipment(self, picking):
        """This Method Used For Cancel The Shipment"""
        tracking_number = [picking.carrier_tracking_ref]
        # if isinstance(tracking_number,dict):
        #     tracking_number = [tracking_number]
        payload = {
            "listNosSuivis": tracking_number
        }
        data = json.dumps(payload)
        _logger.info(data)
        api_key = self.company_id.geodis_api_key  # "12345678"
        timestamp = "%d" % (time.time() * 1000)
        lang = "en"
        service = "api/wsclient/suppression-envois"
        url = "%sapi/wsclient/suppression-envois" % self.company_id.geodis_api_url
        id = self.company_id.geodis_id  # "DEMO"
        hash = self.get_hash(api_key, id, timestamp, lang, service, data)
        token = self.get_token(id, timestamp, lang, hash)
        headers = {'X-GEODIS-Service': token}
        response_data = requests.request("POST", url=url, headers=headers,
                                         data=data)
        _logger.info(">>>>>Cancel Response %s ::::" % response_data.content)
        if response_data.status_code in [200, 201]:
            response_json_data = response_data.json()
            if response_json_data.get('ok') == True:
                return True
            else:
                raise ValidationError(response_json_data)
        else:
            raise ValidationError(response_data.content)

    def geodis_get_tracking_link(self, picking):
        """This Method Is Used For Track The Shippment"""
        return "https://espace-client-tvp.geodis.com/services/destinataires/#/%s/home"%(picking.carrier_tracking_ref)


# Matière dangereuse
# {
#   "noONU": "string",
#   "groupeEmballage": "stri",
#   "classeADR": "string",
#   "codeTypeEmballage": "stri",
#   "nbEmballages": 0,
#   "nomTechnique": "string",
#   "codeQuantite": "PBT",
#   "poidsVolume": 0,
#   "dangerEnv": true
# }

