from odoo import models, fields, _
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    picking_ids = fields.One2many(
        'stock.picking',
        'helpdesk_ticket_id',
        string='Livraisons',
    )
    picking_count = fields.Integer(
        compute='_compute_picking_count',
        string='Nombre de livraisons',
    )

    def _compute_picking_count(self):
        for ticket in self:
            ticket.picking_count = len(ticket.picking_ids)

    def action_create_delivery(self):
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_(
                "Impossible de créer la livraison : "
                "aucun contact n'est renseigné sur le ticket SAV."
            ))

        # Récupère l'adresse de livraison du contact (ou le contact principal si aucune)
        delivery_partner_id = self.partner_id.address_get(['delivery']).get(
            'delivery', self.partner_id.id
        )

        # Recherche le type d'opération "livraison sortante" pour la société courante
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', (self.company_id or self.env.company).id),
        ], limit=1)

        if not picking_type:
            raise UserError(_(
                "Aucun type d'opération de livraison sortante n'a été trouvé "
                "pour cette société."
            ))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': delivery_partner_id,
            'origin': self.name,
            'helpdesk_ticket_id': self.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Livraison'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_pickings(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Livraisons'),
            'res_model': 'stock.picking',
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }
        if self.picking_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.picking_ids[0].id
        return action
