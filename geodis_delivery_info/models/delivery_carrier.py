import json
import logging

from odoo import fields, models

_logger = logging.getLogger("GEODIS")


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def geodis_prepare_request_date(self, pickings):
        request_payload = super().geodis_prepare_request_date(pickings)

        try:
            payload = json.loads(request_payload or '{}')
        except json.JSONDecodeError:
            _logger.warning(
                ">>>>>Delivery Info [%s]: impossible de parser le payload JSON, "
                "instructionLivraison non injectée.",
                pickings.name,
            )
            return request_payload

        list_envois = payload.get('listEnvois') or []
        if not list_envois:
            return request_payload

        # Remplacement par la date du jour
        list_envois[0]['dateDepartEnlevement'] = fields.Date.context_today(self).strftime("%Y-%m-%d")

        # Injection de l'information de livraison
        instruction = pickings.delivery_info or ''
        list_envois[0]['instructionLivraison'] = instruction

        final_payload = json.dumps(payload)
        _logger.info(
            ">>>>>Shipping Request Data WITH instructionLivraison [%s] ::::%s",
            pickings.name,
            final_payload,
        )
        return final_payload
