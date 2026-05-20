import json
import logging
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger("GEODIS")


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def _geodis_next_working_day(self, date):
        """Retourne date + 1 jour, décalé au lundi si le résultat tombe un week-end."""
        next_day = date + timedelta(days=1)
        if next_day.weekday() == 5:    # Samedi → Lundi
            next_day += timedelta(days=2)
        elif next_day.weekday() == 6:  # Dimanche → Lundi
            next_day += timedelta(days=1)
        return next_day

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

        # dateDepartEnlevement = date du jour
        date_today = fields.Date.context_today(self)
        list_envois[0]['dateDepartEnlevement'] = date_today.strftime("%Y-%m-%d")

        # dateLivraison = date saisie par l'utilisateur, ou J+1 ouvré par défaut
        if self.option_livraison != 'RDW':
            if not pickings.date_enlevement_souhaitee_jf:
                pickings.date_enlevement_souhaitee_jf = self._geodis_next_working_day(date_today)
            list_envois[0]['dateLivraison'] = pickings.date_enlevement_souhaitee_jf.strftime("%Y-%m-%d")

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
