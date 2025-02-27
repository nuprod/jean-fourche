from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class NuprodSaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_method_selected_for_sale = fields.Many2one(
        'payment.method',
        string="Méthode de paiement du client",
        compute="_compute_get_payment_method",
        store=True
    )

    @api.depends('state')
    def _compute_get_payment_method(self):
        for record in self:
            # Recherche de la transaction de paiement associée à la commande
            payment_transaction_type = self.env["payment.transaction"].search([('reference', '=', record.name)], limit=1)

            if payment_transaction_type and payment_transaction_type.payment_method_id:

                    record.payment_method_selected_for_sale = payment_transaction_type.payment_method_id

                    if record.payment_method_selected_for_sale:
                        payment_term = self.env['account.payment.term'].search([('payment_method_id', '=', record.payment_method_selected_for_sale.id)], limit=1)

                        if payment_term:
                            record.payment_term_id = payment_term.id
                            _logger.warning(f"Assignation de {record.payment_term_id.name} reussi pour la commande {record.name}")

                        else:
                            _logger.error(f"Aucune méthode de paiment trouvé dans account.payment.term pour {record.payment_method_selected_for_sale.id}")

                    else:
                        _logger.error(f"Aucun methode de transaction selectionné")

