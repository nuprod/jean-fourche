# -*- coding: utf-8 -*-
"""
Étiquette de retour Chronopost 2Shop (5Y "2Shop Retour" / 6C "2Shop Retour Europe").

Flux inversé par rapport à un envoi classique (cf. mail Chronopost IT-17588) :
- shipperValue  = le client final, avec son adresse personnelle,
- customerValue = la société (donneur d'ordre),
- recipientValue = l'adresse de retour de la société.
Ça ne correspond à aucune expédition sortante existante dans Odoo, d'où un
assistant dédié plutôt qu'un branchement sur chronopost_provider_send_shipping.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.delivery_carrier import CHRONOPOST_2SHOP_EUROPE_CODES, CHRONOPOST_2SHOP_RETURN_CODES


class ChronopostReturnLabelWizard(models.TransientModel):
    _name = "chronopost.return.label.wizard"
    _description = "Étiquette de retour Chronopost 2Shop"

    sale_order_id = fields.Many2one("sale.order", string="Commande d'origine")
    carrier_id = fields.Many2one(
        "delivery.carrier", string="Offre Chronopost", required=True,
        domain=[("delivery_type", "=", "chronopost_provider"), ("chronopost_product_code", "in", list(CHRONOPOST_2SHOP_RETURN_CODES))],
    )
    partner_id = fields.Many2one("res.partner", string="Client (expéditeur du retour)", required=True)
    return_partner_id = fields.Many2one(
        "res.partner", string="Destinataire du retour (société)",
        help="Adresse de retour de la société. Par défaut celle configurée sur l'offre Chronopost, "
             "sinon l'adresse de l'entrepôt courant.",
    )
    weight = fields.Float(string="Poids (kg)", required=True)
    height = fields.Float(string="Hauteur (cm)")
    length = fields.Float(string="Longueur (cm)")
    width = fields.Float(string="Largeur (cm)")
    number_of_parcel = fields.Integer(string="Nombre de colis", default=1)
    content1 = fields.Char(
        string="Contenu du colis (EN)",
        help="Obligatoire pour 2Shop Retour Europe : description en anglais, précise et non générique "
             "de l'article principal du colis.",
    )
    customs_value = fields.Float(string="Valeur douane")
    state = fields.Selection([("draft", "Brouillon"), ("done", "Étiquette générée")], default="draft")
    tracking_number = fields.Char(readonly=True)
    label_data = fields.Binary(readonly=True)
    label_filename = fields.Char(readonly=True)

    def _default_return_partner(self):
        if self.carrier_id.chronopost_return_partner_id:
            return self.carrier_id.chronopost_return_partner_id
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.carrier_id.company_id.id)], limit=1)
        return warehouse.partner_id

    @api.onchange("carrier_id")
    def onchange_carrier_id(self):
        for wizard in self:
            if wizard.carrier_id and not wizard.return_partner_id:
                wizard.return_partner_id = wizard._default_return_partner()

    def action_generate_label(self):
        self.ensure_one()
        carrier = self.carrier_id
        code = carrier.chronopost_product_code
        if code not in CHRONOPOST_2SHOP_RETURN_CODES:
            raise UserError(_("L'offre sélectionnée n'est pas une offre de retour 2Shop (5Y/6C)."))
        if not self.weight:
            raise UserError(_("Le poids est obligatoire."))
        return_partner = self.return_partner_id or self._default_return_partner()
        if not return_partner:
            raise UserError(_(
                "Aucune adresse de retour n'est configurée : renseignez le champ \"Adresse de retour 2Shop\" "
                "sur l'offre Chronopost %s."
            ) % carrier.display_name)

        content1 = ""
        customs_value = ""
        if code in CHRONOPOST_2SHOP_EUROPE_CODES:
            if not self.content1:
                raise UserError(_(
                    "Le contenu du colis (en anglais, non générique) est obligatoire pour 2Shop Retour Europe."
                ))
            content1 = self.content1
            customs_value = "%.2f" % (self.customs_value or 0.0)

        service = carrier._chronopost_2shop_service(code, self.weight)
        company = carrier.company_id

        vals = {
            "header": {"accountNumber": carrier._chronopost_2shop_account_number(), "idEmit": "CHRFR"},
            "shipper": {
                "shipperAdress1": self.partner_id.street, "shipperAdress2": self.partner_id.street2,
                "shipperCity": self.partner_id.city, "shipperCivility": "M",
                "shipperContactName": self.partner_id.name, "shipperCountry": self.partner_id.country_id.code,
                "shipperCountryName": self.partner_id.country_id.name, "shipperEmail": self.partner_id.email,
                "shipperMobilePhone": self.partner_id.mobile, "shipperName": self.partner_id.name,
                "shipperPhone": self.partner_id.phone, "shipperPreAlert": "0",
                "shipperZipCode": self.partner_id.zip, "shipperType": "1",
            },
            "customer": {
                "customerAdress1": company.street, "customerAdress2": company.street2,
                "customerCity": company.city, "customerCivility": "M",
                "customerContactName": company.name, "customerCountry": company.country_id.code,
                "customerCountryName": company.country_id.name, "customerEmail": company.email,
                "customerName": company.name, "customerPhone": company.phone,
                "customerPreAlert": "0", "customerZipCode": company.zip, "printAsSender": "N",
            },
            "recipient": {
                "recipientName": return_partner.name, "recipientAdress1": return_partner.street,
                "recipientAdress2": return_partner.street2, "recipientZipCode": return_partner.zip,
                "recipientCity": return_partner.city, "recipientCountry": return_partner.country_id.code,
                "recipientContactName": return_partner.name, "recipientEmail": return_partner.email,
                "recipientPhone": return_partner.phone, "recipientMobilePhone": return_partner.mobile,
                "recipientPreAlert": "0",
                "recipientType": carrier._chronopost_2shop_recipient_type(code),
            },
            "ref": {
                "recipientRef": self.partner_id.ref or "",
                "shipperRef": (self.sale_order_id.name if self.sale_order_id else "") or "",
            },
            "skybill": {
                "bulkNumber": "1", "codCurrency": "EUR", "codValue": "0",
                "content1": content1, "customsCurrency": company.currency_id.name,
                "customsValue": customs_value, "evtCode": "DC", "insuredCurrency": "EUR",
                "insuredValue": "0", "objectType": carrier.chronopost_package_type or "MAR",
                "portValue": "0", "productCode": code, "service": service,
                "shipDate": fields.Date.today().strftime("%Y-%m-%d"),
                "shipHour": fields.Datetime.now().strftime("%H"),
                "skybillRank": "1", "weight": str(self.weight), "weightUnit": "KGM",
                "height": str(self.height or 0), "length": str(self.length or 0), "width": str(self.width or 0),
                "as": carrier._chronopost_2shop_as_code(code), "carrier": "1",
            },
            # PPR : impression A4 avec liste des points relais de dépose, obligatoire pour les retours 2Shop.
            "skybill_params": {"duplicata": "N", "mode": "PPR", "withReservation": carrier.chronopost_with_reservation or "2"},
            "top": {
                "password": carrier._chronopost_2shop_password(),
                "modeRetour": carrier.chronopost_mode_retour or "2",
                "numberOfParcel": str(self.number_of_parcel or 1),
                "version": "2.0",
                "multiParcel": "Y" if (self.number_of_parcel or 1) > 1 else "N",
            },
        }

        envelope = carrier._chronopost_v4_build_envelope(vals)
        parcels = carrier._chronopost_v4_call_and_process(envelope)
        if not parcels:
            raise ValidationError(_("Chronopost n'a retourné aucune étiquette."))

        main_parcel = parcels[0]
        self.tracking_number = ",".join(p["skybill_number"] for p in parcels)
        self.state = "done"
        if main_parcel["label_base64"]:
            self.label_data = main_parcel["label_base64"].encode()
            self.label_filename = "LabelReturn-chronopost-2shop-%s.pdf" % main_parcel["skybill_number"]
            if self.sale_order_id and main_parcel["label_binary"]:
                self.sale_order_id.message_post(
                    body=_("Étiquette de retour Chronopost générée : %s") % self.tracking_number,
                    attachments=[(self.label_filename, main_parcel["label_binary"])],
                )

        return {
            "type": "ir.actions.act_window",
            "res_model": "chronopost.return.label.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
