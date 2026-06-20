from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

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
        grouped_data = self.env['stock.picking'].read_group(
            [('helpdesk_ticket_id', 'in', self.ids)],
            ['helpdesk_ticket_id'],
            ['helpdesk_ticket_id']
        )

        counts = {
            data['helpdesk_ticket_id'][0]: data['helpdesk_ticket_id_count']
            for data in grouped_data
        }

        for ticket in self:
            ticket.picking_count = counts.get(ticket.id, 0)

    def action_create_delivery(self):
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_(
                "Impossible de créer la livraison : "
                "aucun contact n'est renseigné sur le ticket SAV."
            ))

        delivery_partner_id = self.partner_id.address_get(['delivery']).get(
            'delivery', self.partner_id.id
        )

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', (self.company_id or self.env.company).id),
        ], limit=1)

        if not picking_type:
            raise UserError(_(
                "Aucun type d'opération de livraison sortante n'a été trouvé "
                "pour cette société."
            ))

        delivery_partner = self.env['res.partner'].browse(delivery_partner_id)

        location_dest = (
            delivery_partner.property_stock_customer
            or self.partner_id.commercial_partner_id.property_stock_customer
            or self.env.ref('stock.stock_location_customers')
        )

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': delivery_partner_id,
            'origin': f"Ticket Assistance - {self.ticket_ref or self.name or self.id}",
            'helpdesk_ticket_id': self.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': location_dest.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Livraison'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_replaces(self):
        self.ensure_one()
    
        _logger.info("Action view pickings appelée pour ticket ID=%s / name=%s", self.id, self.display_name)
    
        pickings = self.env['stock.picking'].search([
            ('helpdesk_ticket_id', '=', self.id)
        ])
    
        _logger.info(
            "Pickings trouvés pour ticket ID=%s : count=%s / ids=%s",
            self.id,
            len(pickings),
            pickings.ids
        )
    
        _logger.info(
            "Valeurs ticket : picking_count=%s / picking_ids=%s",
            self.picking_count,
            self.picking_ids.ids
        )
    
        if len(pickings) == 1:
            _logger.info("Ouverture du picking unique ID=%s", pickings.id)
            return {
                'type': 'ir.actions.act_window',
                'name': _('Livraison'),
                'res_model': 'stock.picking',
                'res_id': pickings.id,
                'view_mode': 'form',
                'target': 'current',
            }
    
        _logger.info("Ouverture de la liste des pickings : %s", pickings.ids)
    
        return {
            'type': 'ir.actions.act_window',
            'name': _('Livraisons'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', pickings.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }