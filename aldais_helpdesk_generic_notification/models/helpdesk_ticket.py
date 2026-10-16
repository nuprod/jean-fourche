from odoo import models


class GenericMessage:
    """ Message présenté au layout de notification : délègue tout au vrai
    message sauf son corps et son aperçu. """

    def __init__(self, message, body):
        self._message = message
        self.body = body
        self.preview = ''

    def __getattr__(self, name):
        return getattr(self._message, name)


# groupes de destinataires recevant le message générique : le client du ticket
# ('portal_customer', ajouté par portal) et les contacts de sa société
CUSTOMER_GROUPS = ('portal_customer', 'helpdesk_customer_portal', 'helpdesk_customer')


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _get_customer_partner_ids(self):
        """ Le client du ticket et tous les contacts de sa société. Les autres
        destinataires externes (fournisseurs, réparateurs...) reçoivent le
        mail complet. """
        commercial_partner = self.partner_id.commercial_partner_id
        if not commercial_partner:
            return set()
        return set(self.env['res.partner'].sudo().with_context(active_test=False).search([
            ('id', 'child_of', commercial_partner.id),
        ]).ids)

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        groups = super()._notify_get_recipients_groups(
            message, model_description, msg_vals=msg_vals,
        )
        if not self:
            return groups
        customer_ids = self._get_customer_partner_ids()
        if not customer_ids:
            return groups
        new_groups = [
            ('helpdesk_customer_portal',
             lambda pdata: pdata['id'] in customer_ids and pdata['type'] == 'portal',
             {'active': True, 'has_button_access': True}),
            ('helpdesk_customer',
             lambda pdata: pdata['id'] in customer_ids and pdata['type'] == 'customer',
             {'active': True, 'has_button_access': False}),
        ]
        index = next((i + 1 for i, group in enumerate(groups) if group[0] == 'portal_customer'), 0)
        return groups[:index] + new_groups + groups[index:]

    def _notify_by_email_render_layout(self, message, recipients_group,
                                       msg_vals=False, render_values=None):
        """ Les clients reçoivent un message générique à la place du contenu du
        message, pour les obliger à passer par le portail pour lire et répondre.
        Le message lui-même (chatter, portail) n'est pas modifié. """
        if not self or recipients_group.get('notification_group_name') not in CUSTOMER_GROUPS:
            return super()._notify_by_email_render_layout(
                message, recipients_group, msg_vals=msg_vals, render_values=render_values,
            )
        self.ensure_one()
        render_values = dict(render_values or {})
        email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
        generic_body = self.env['ir.qweb']._render(
            'aldais_helpdesk_generic_notification.ticket_generic_notification_body',
            {
                **render_values,
                **recipients_group,
                # le layout standard affiche déjà le bouton d'accès en en-tête
                'show_body_button': recipients_group.get('has_button_access')
                and bool(email_layout_xmlid) and email_layout_xmlid != 'mail.mail_notification_layout',
            },
            minimal_qcontext=True,
            lang=render_values.get('lang', self.env.lang),
        )
        render_values['message'] = GenericMessage(message, generic_body)
        render_values['tracking_values'] = []
        render_values['signature'] = ''
        render_values['email_add_signature'] = False
        return super()._notify_by_email_render_layout(
            message, recipients_group, msg_vals=msg_vals, render_values=render_values,
        )

    def _notify_by_email_get_final_mail_values(self, recipient_ids, mail_values,
                                               additional_values=None):
        """ Pas de pièces jointes dans les mails envoyés aux clients : elles sont
        consultables depuis le ticket sur le portail. """
        values = super()._notify_by_email_get_final_mail_values(
            recipient_ids, mail_values, additional_values=additional_values,
        )
        if self and self._get_customer_partner_ids() & set(recipient_ids):
            values['send_without_attachments'] = True
        return values
