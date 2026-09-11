# -*- coding: utf-8 -*-
"""
Support des offres Chronopost 2Shop (webservice shippingMultiParcelV4).

chronopost_shipping_integration (module Vraja) n'implémente que le webservice
shippingMultiParcel v1, dont le schéma XML ne couvre pas les offres 2Shop :
il manque notamment idRelais, recipientName2, la balise <as> (code AS) et
<content1> (déclaration douane), et les codes produit/service 2Shop ne sont
pas dans les Selection du module.

Ce fichier ajoute :
- les 4 codes produit 2Shop et le mode d'impression PPR aux Selection existantes,
- un générateur générique pour le XML shippingMultiParcelV4 (utilisé aussi bien
  pour l'envoi 2Shop Direct/Europe que par l'assistant de retour, cf. wizard/),
- la bascule de chronopost_provider_send_shipping vers ce nouveau flux quand
  le code produit du transporteur est 5X ou 6B (le flux v1 existant n'est pas
  touché pour les autres codes produit).
"""
import binascii
import logging
import xml.etree.ElementTree as etree

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger("Chronopost2Shop")

# Codes produit 2Shop et leurs paramètres fixes, tels que documentés par
# Chronopost (mail IT-17588 du 10/09/2026 + échantillons de requêtes fournis).
CHRONOPOST_2SHOP_OUTBOUND_CODES = ("5X", "6B")  # envoi vers point relais
CHRONOPOST_2SHOP_RETURN_CODES = ("5Y", "6C")  # retour client -> société
CHRONOPOST_2SHOP_EUROPE_CODES = ("6B", "6C")  # content1 douane obligatoire

_2SHOP_AS_CODE = {"5X": "", "5Y": "A15", "6B": "", "6C": ""}
_2SHOP_RECIPIENT_TYPE = {"5X": "2", "5Y": "1", "6B": "2", "6C": "2"}

# Ordre des balises tel qu'observé dans les échantillons de requêtes Chronopost
# (les PJ jointes au ticket IT-17588). On le respecte au cas où le WS serait
# sensible à l'ordre des éléments.
_V4_SECTION_FIELDS = {
    "headerValue": ["accountNumber", "idEmit", "identWebPro", "subAccount"],
    "shipperValue": [
        "shipperAdress1", "shipperAdress2", "shipperCity", "shipperCivility",
        "shipperContactName", "shipperCountry", "shipperCountryName", "shipperEmail",
        "shipperMobilePhone", "shipperName", "shipperName2", "shipperPhone",
        "shipperPreAlert", "shipperZipCode", "shipperType",
    ],
    "customerValue": [
        "customerAdress1", "customerAdress2", "customerCity", "customerCivility",
        "customerContactName", "customerCountry", "customerCountryName", "customerEmail",
        "customerMobilePhone", "customerName", "customerName2", "customerPhone",
        "customerPreAlert", "customerZipCode", "printAsSender",
    ],
    "recipientValue": [
        "recipientName", "recipientName2", "recipientAdress1", "recipientAdress2",
        "recipientZipCode", "recipientCity", "recipientCountry", "recipientContactName",
        "recipientEmail", "recipientPhone", "recipientMobilePhone", "recipientPreAlert",
        "recipientType",
    ],
    "refValue": ["customerSkybillNumber", "recipientRef", "shipperRef", "idRelais"],
    "skybillValue": [
        "bulkNumber", "codCurrency", "codValue", "content1", "content2", "content3",
        "content4", "content5", "customsCurrency", "customsValue", "evtCode",
        "insuredCurrency", "insuredValue", "latitude", "longitude", "masterSkybillNumber",
        "objectType", "portCurrency", "portValue", "productCode", "qualite", "service",
        "shipDate", "shipHour", "skybillRank", "source", "weight", "weightUnit", "height",
        "length", "width", "as", "subAccount", "toTheOrderOf", "skybillNumber", "carrier",
        "skybillBackNumber", "alternateProductCode", "labelNumber",
    ],
    "skybillParamsValue": ["duplicata", "mode", "withReservation"],
}
_V4_TOP_LEVEL_FIELDS = ["password", "modeRetour", "numberOfParcel", "version", "multiParcel"]
# Clé attendue dans le dict `vals` passé à _chronopost_v4_build_envelope, pour chaque section XML.
_V4_SECTION_VALS_KEY = {
    "headerValue": "header",
    "shipperValue": "shipper",
    "customerValue": "customer",
    "recipientValue": "recipient",
    "refValue": "ref",
    "skybillValue": "skybill",
    "skybillParamsValue": "skybill_params",
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    chronopost_product_code = fields.Selection(
        selection_add=[
            ("5X", "2Shop Direct"),
            ("5Y", "2Shop Retour"),
            ("6B", "2Shop Europe"),
            ("6C", "2Shop Retour Europe"),
        ],
        # "set default" nécessite un default défini sur le champ de base, ce qui n'est pas le cas ici ;
        # "cascade" (défaut Odoo pour un champ sans valeur de repli) supprime le transporteur concerné
        # si ce module est un jour désinstallé, ce qui reste acceptable pour ce cas d'usage.
        ondelete={"5X": "cascade", "5Y": "cascade", "6B": "cascade", "6C": "cascade"},
    )
    chronopost_label_mode = fields.Selection(selection_add=[("PPR", "PPR (retour A4)")], ondelete={"PPR": "cascade"})
    chronopost_return_partner_id = fields.Many2one(
        "res.partner", string="Adresse de retour 2Shop",
        help="Adresse à laquelle Chronopost doit livrer les retours 2Shop Retour / 2Shop Retour Europe "
             "(recipientValue de l'étiquette de retour). Si non renseigné, l'adresse de l'entrepôt est utilisée.",
    )
    chronopost_2shop_account_number = fields.Char(
        string="N° de compte Chronopost 2Shop",
        help="À renseigner uniquement si ce contrat 2Shop utilise des identifiants Chronopost différents "
             "du contrat standard (champ Compte Société > Chronopost). Laisser vide pour réutiliser les "
             "identifiants de la société.",
    )
    chronopost_2shop_password = fields.Char(
        string="Mot de passe Chronopost 2Shop",
        help="Idem chronopost_2shop_account_number : laisser vide pour réutiliser le mot de passe société.",
    )

    def _chronopost_2shop_account_number(self):
        self.ensure_one()
        return self.chronopost_2shop_account_number or self.company_id.chronopost_account_number

    def _chronopost_2shop_password(self):
        self.ensure_one()
        return self.chronopost_2shop_password or self.company_id.chronopost_password

    # ------------------------------------------------------------------
    # Bascule du flux d'envoi standard vers le générateur 2Shop
    # ------------------------------------------------------------------
    def chronopost_provider_send_shipping(self, picking):
        self.ensure_one()
        if self.chronopost_product_code in CHRONOPOST_2SHOP_OUTBOUND_CODES:
            return self._chronopost_2shop_send_shipping(picking)
        if self.chronopost_product_code in CHRONOPOST_2SHOP_RETURN_CODES:
            raise ValidationError(_(
                "Les offres 2Shop Retour et 2Shop Retour Europe ne se génèrent pas depuis le bouton "
                "d'envoi standard : utilisez l'assistant \"Étiquette de retour Chronopost\"."
            ))
        return super().chronopost_provider_send_shipping(picking)

    def _chronopost_2shop_send_shipping(self, picking):
        """2Shop Direct (5X) / 2Shop Europe (6B) : envoi entrepôt -> point relais choisi par le client."""
        self.ensure_one()
        code = self.chronopost_product_code
        shipper = picking.picking_type_id.warehouse_id.partner_id
        customer = picking.partner_id
        point = picking.sale_id and picking.sale_id.chronopost_set_pickup_point_id
        if not point:
            raise ValidationError(_(
                "Aucun point relais n'a été sélectionné sur la commande liée à cette expédition "
                "(onglet Chronopost Pickup Locations : Get Locations puis Set Location)."
            ))
        shipper_error = self.check_address_details(shipper, ["zip", "city", "country_id", "street"])
        if shipper_error or not picking.shipping_weight:
            raise ValidationError("%s%s" % (
                "Adresse expéditeur : %s\n" % shipper_error if shipper_error else "",
                "Poids d'expédition manquant !" if not picking.shipping_weight else "",
            ))

        weight = picking.shipping_weight
        service = self._chronopost_2shop_service(code, weight)
        content1 = ""
        customs_value = ""
        if code in CHRONOPOST_2SHOP_EUROPE_CODES:
            content1 = self._chronopost_2shop_get_content1(picking.move_ids)
            customs_value = "%.2f" % sum(
                (m.product_id.list_price or 0.0) * (m.quantity or m.product_uom_qty or 0.0)
                for m in picking.move_ids
            )

        vals = {
            "header": {
                "accountNumber": self._chronopost_2shop_account_number(),
                "idEmit": "CHRFR",
            },
            "shipper": {
                "shipperAdress1": shipper.street, "shipperAdress2": shipper.street2,
                "shipperCity": shipper.city, "shipperCivility": self.chronopost_shipper_civility,
                "shipperContactName": shipper.name, "shipperCountry": shipper.country_id.code,
                "shipperCountryName": shipper.country_id.name, "shipperEmail": shipper.email,
                "shipperMobilePhone": shipper.mobile, "shipperName": shipper.name,
                "shipperPhone": shipper.phone, "shipperPreAlert": "0",
                "shipperZipCode": shipper.zip, "shipperType": "1",
            },
            "customer": {
                "customerAdress1": customer.street, "customerAdress2": customer.street2,
                "customerCity": customer.city, "customerCivility": "M",
                "customerContactName": customer.name, "customerCountry": customer.country_id.code,
                "customerCountryName": customer.country_id.name, "customerEmail": customer.email,
                "customerMobilePhone": customer.mobile, "customerName": customer.name,
                "customerPhone": customer.phone, "customerPreAlert": "0",
                "customerZipCode": customer.zip, "printAsSender": "N",
            },
            "recipient": {
                "recipientName": point.name, "recipientName2": customer.name,
                "recipientAdress1": point.street, "recipientAdress2": point.street2,
                "recipientZipCode": point.zip, "recipientCity": point.city,
                "recipientCountry": point.country_id.code, "recipientContactName": customer.name,
                "recipientEmail": customer.email, "recipientPhone": customer.phone,
                "recipientMobilePhone": customer.mobile, "recipientPreAlert": "0",
                "recipientType": self._chronopost_2shop_recipient_type(code),
            },
            "ref": {
                "recipientRef": customer.ref or "", "shipperRef": picking.name or "",
                "idRelais": point.point_identifier or "",
            },
            "skybill": {
                "bulkNumber": "1", "codCurrency": "EUR", "codValue": "0",
                "content1": content1, "customsCurrency": self.company_id.currency_id.name,
                "customsValue": customs_value, "evtCode": "DC", "insuredCurrency": "EUR",
                "insuredValue": "0", "masterSkybillNumber": "", "objectType": self.chronopost_package_type,
                "portValue": "0", "productCode": code, "service": service,
                "shipDate": picking.scheduled_date.strftime("%Y-%m-%d"),
                "shipHour": fields.Datetime.now().strftime("%H"),
                "skybillRank": "1", "weight": str(weight), "weightUnit": "KGM",
                "height": str(self.chronopost_provider_package_id.height or 0),
                "length": str(self.chronopost_provider_package_id.packaging_length or 0),
                "width": str(self.chronopost_provider_package_id.width or 0),
                "as": self._chronopost_2shop_as_code(code), "carrier": "1",
            },
            "skybill_params": {
                "duplicata": "N", "mode": self.chronopost_label_mode,
                "withReservation": self.chronopost_with_reservation,
            },
            "top": {
                "password": self._chronopost_2shop_password(),
                "modeRetour": self.chronopost_mode_retour,
                "numberOfParcel": str(picking.chronopost_number_of_parcel or 1),
                "version": "2.0",
                "multiParcel": "Y" if (picking.chronopost_number_of_parcel or 1) > 1 else "N",
            },
        }

        envelope = self._chronopost_v4_build_envelope(vals)
        parcels = self._chronopost_v4_call_and_process(envelope)

        tracking_numbers = []
        for index, parcel in enumerate(parcels, start=1):
            tracking_numbers.append(parcel["skybill_number"])
            if parcel["label_binary"]:
                picking.message_post(attachments=[
                    ("LabelShipping-chronopost-2shop-%s.%s" % (index, self.chronopost_label_mode), parcel["label_binary"])
                ])
        return [{"exact_price": 0.0, "tracking_number": ",".join(tracking_numbers)}]

    # ------------------------------------------------------------------
    # Helpers partagés (aussi utilisés par le wizard de retour)
    # ------------------------------------------------------------------
    def _chronopost_2shop_service(self, product_code, weight):
        if product_code == "5X":
            return "6"
        if product_code == "5Y":
            return "6"
        if product_code == "6C":
            return "332"
        if product_code == "6B":
            # Chronopost : "2Shop Europe - de 3Kg" -> 338, "2Shop Europe + de 3Kg" -> 337
            return "338" if weight < 3 else "337"
        raise ValidationError(_("Code produit 2Shop inconnu : %s") % product_code)

    def _chronopost_2shop_recipient_type(self, product_code):
        return _2SHOP_RECIPIENT_TYPE[product_code]

    def _chronopost_2shop_as_code(self, product_code):
        return _2SHOP_AS_CODE[product_code]

    def _chronopost_2shop_get_content1(self, moves):
        """<content1> : détail (en anglais, non générique) de l'article le plus significatif du colis
        (le plus cher ou le plus en nombre), obligatoire pour les colis intra UE / Relais Europe.
        Renseigné via le champ product.template.chronopost_customs_description.
        """
        moves = moves.filtered(lambda m: m.product_id.type == "product" and (m.quantity or m.product_uom_qty))
        if not moves:
            raise ValidationError(_("Impossible de déterminer le contenu du colis (aucune ligne de mouvement)."))
        main_move = max(moves, key=lambda m: (m.product_id.list_price or 0.0) * (m.quantity or m.product_uom_qty or 0.0))
        description = main_move.product_id.chronopost_customs_description
        if not description:
            raise ValidationError(_(
                "Le produit \"%s\" n'a pas de description douanière Chronopost (en anglais, non générique) : "
                "renseignez le champ \"Désignation douane Chronopost (EN)\" sur sa fiche produit."
            ) % main_move.product_id.display_name)
        return description

    def _chronopost_v4_build_envelope(self, vals):
        """Construit l'enveloppe SOAP shippingMultiParcelV4 à partir de `vals`
        (dict de sous-dicts par section, cf. clés dans _V4_SECTION_FIELDS/_V4_TOP_LEVEL_FIELDS)."""
        root = etree.Element("soapenv:Envelope")
        root.attrib["xmlns:soapenv"] = "http://schemas.xmlsoap.org/soap/envelope/"
        root.attrib["xmlns:cxf"] = "http://cxf.shipping.soap.chronopost.fr/"
        etree.SubElement(root, "soapenv:Header")
        body = etree.SubElement(root, "soapenv:Body")
        envelope = etree.SubElement(body, "cxf:shippingMultiParcelV4")

        for section_tag, field_names in _V4_SECTION_FIELDS.items():
            section_node = etree.SubElement(envelope, section_tag)
            section_data = vals.get(_V4_SECTION_VALS_KEY[section_tag], {})
            for field_name in field_names:
                etree.SubElement(section_node, field_name).text = str(section_data.get(field_name, "") or "")

        top_data = vals.get("top", {})
        for field_name in _V4_TOP_LEVEL_FIELDS:
            etree.SubElement(envelope, field_name).text = str(top_data.get(field_name, "") or "")

        return root

    def _chronopost_v4_call_and_process(self, root_node_envelope):
        """Envoie l'enveloppe shippingMultiParcelV4 et retourne une liste de
        {'skybill_number': str, 'label_base64': str, 'label_binary': bytes|None}."""
        self.ensure_one()
        header = {"Content-Type": "application/xml"}
        api_url = "{}/shipping-cxf/ShippingServiceWS".format(self.company_id.chronopost_api_url)
        request_data = etree.tostring(root_node_envelope)
        response_status, response_data = self.chronopost_provider_create_shipment("POST", api_url, request_data, header)
        if not response_status:
            raise ValidationError(response_data)

        body = (response_data.get("Envelope") or {}).get("Body") or {}
        ret = (body.get("shippingMultiParcelV4Response") or {}).get("return")
        if not ret:
            raise ValidationError(response_data)
        error_code = ret.get("errorCode")
        if error_code not in (None, "0"):
            raise ValidationError(ret.get("errorMessage") or _("Erreur Chronopost 2Shop (code %s)") % error_code)

        result = ret.get("resultMultiParcelValue")
        if not result:
            raise ValidationError(ret.get("errorMessage") or response_data)
        parcels = result if isinstance(result, list) else [result]

        processed = []
        for parcel in parcels:
            label_b64 = parcel.get("pdfEtiquette")
            processed.append({
                "skybill_number": parcel.get("skybillNumber"),
                "label_base64": label_b64,
                "label_binary": binascii.a2b_base64(str(label_b64)) if label_b64 else None,
            })
        return processed
