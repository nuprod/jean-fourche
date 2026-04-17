import json

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def geodis_prepare_request_date(self, pickings):
        request_payload = super().geodis_prepare_request_date(pickings)

        try:
            payload = json.loads(request_payload or '{}')
        except json.JSONDecodeError:
            return request_payload

        if not pickings.package_ids:
            return request_payload

        dangerous_goods = pickings._build_geodis_dangerous_goods_list()
        if not dangerous_goods:
            return request_payload

        list_envois = payload.get('listEnvois') or []
        if not list_envois:
            return request_payload

        list_envois[0]['listMatieresDangereuses'] = dangerous_goods
        return json.dumps(payload)
