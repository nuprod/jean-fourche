import json

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dangerous_goods_json = fields.Text(
        string='Dangerous Goods JSON',
        compute='_compute_dangerous_goods_json',
        readonly=True,
    )

    @api.depends(
        'package_ids',
        'package_ids.name',
        'move_line_ids.quantity',
        'move_line_ids.result_package_id',
        'move_line_ids.product_id',
        'move_line_ids.product_id.dangerous_goods_line_ids',
        'move_line_ids.product_id.dangerous_goods_line_ids.no_onu',
        'move_line_ids.product_id.dangerous_goods_line_ids.groupe_emballage',
        'move_line_ids.product_id.dangerous_goods_line_ids.classe_adr',
        'move_line_ids.product_id.dangerous_goods_line_ids.code_type_emballage',
        'move_line_ids.product_id.dangerous_goods_line_ids.nom_technique',
        'move_line_ids.product_id.dangerous_goods_line_ids.code_quantite',
        'move_line_ids.product_id.dangerous_goods_line_ids.danger_env',
        'move_line_ids.product_id.dangerous_goods_line_ids.poids_matiere_dangereuse',
    )
    def _compute_dangerous_goods_json(self):
        for picking in self:
            debug_payload = picking._build_dangerous_goods_debug_payload()
            picking.dangerous_goods_json = json.dumps(debug_payload, indent=2, ensure_ascii=False, sort_keys=True)

    def _get_packaged_quantities_by_package(self):
        self.ensure_one()
        packaged_quantities = {}
        package_ids = self.package_ids
        if not package_ids:
            return packaged_quantities

        packaged_move_lines = self.move_line_ids.filtered(
            lambda ml: ml.result_package_id in package_ids and ml.quantity > 0 and ml.product_id
        )

        for move_line in packaged_move_lines:
            package = move_line.result_package_id
            package_bucket = packaged_quantities.setdefault(package, {})
            product = move_line.product_id
            package_bucket[product] = package_bucket.get(product, 0.0) + move_line.qty_done

        return packaged_quantities

    def _aggregate_dangerous_goods_by_onu(self):
        self.ensure_one()
        aggregated = {}

        for package, products_qty in self._get_packaged_quantities_by_package().items():
            for product, qty in products_qty.items():
                for adr_line in product.dangerous_goods_line_ids:
                    onu_key = adr_line.no_onu
                    if not onu_key:
                        continue
                    item = aggregated.setdefault(
                        onu_key,
                        {
                            'no_onu': onu_key,
                            'groupe_emballage': adr_line.groupe_emballage or '',
                            'classe_adr': adr_line.classe_adr or '',
                            'code_type_emballage': adr_line.code_type_emballage or '',
                            'nom_technique': adr_line.nom_technique or '',
                            'code_quantite': adr_line.code_quantite or '',
                            'danger_env': bool(adr_line.danger_env),
                            'poids_volume': 0.0,
                            'package_ids': set(),
                        },
                    )
                    item['poids_volume'] += adr_line.poids_matiere_dangereuse * qty
                    item['package_ids'].add(package)

        return aggregated

    def _build_geodis_dangerous_goods_list(self):
        self.ensure_one()
        aggregated = self._aggregate_dangerous_goods_by_onu()
        payload_list = []

        for onu_key in sorted(aggregated):
            item = aggregated[onu_key]
            payload_list.append(
                {
                    'noONU': item['no_onu'],
                    'groupeEmballage': item['groupe_emballage'],
                    'classeADR': item['classe_adr'],
                    'codeTypeEmballage': item['code_type_emballage'],
                    'nbEmballages': len(item['package_ids']),
                    'nomTechnique': item['nom_technique'],
                    'codeQuantite': item['code_quantite'],
                    'poidsVolume': round(item['poids_volume'], 6),
                    'dangerEnv': item['danger_env'],
                }
            )

        return payload_list

    def _build_dangerous_goods_debug_payload(self):
        self.ensure_one()
        aggregated = self._aggregate_dangerous_goods_by_onu()
        onu_lines = []

        for onu_key in sorted(aggregated):
            item = aggregated[onu_key]
            package_names = sorted(pkg.name or str(pkg.id) for pkg in item['package_ids'])
            onu_lines.append(
                {
                    'no_onu': item['no_onu'],
                    'groupe_emballage': item['groupe_emballage'],
                    'classe_adr': item['classe_adr'],
                    'code_type_emballage': item['code_type_emballage'],
                    'nom_technique': item['nom_technique'],
                    'code_quantite': item['code_quantite'],
                    'danger_env': item['danger_env'],
                    'nb_emballages': len(item['package_ids']),
                    'poids_volume': round(item['poids_volume'], 6),
                    'packages': package_names,
                }
            )

        return {
            'picking': self.name,
            'line_count': len(onu_lines),
            'list_matieres_dangereuses': onu_lines,
        }
