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


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _has_external_recipients(self, partner_ids):
        return any(self.env['res.partner'].sudo().browse(partner_ids).mapped('partner_share'))

    def _notify_by_email_render_layout(self, message, recipients_group,
                                       msg_vals=False, render_values=None):
        """ Les clients reçoivent un message générique à la place du contenu du
        message, pour les obliger à passer par le portail pour lire et répondre.
        Le message lui-même (chatter, portail) n'est pas modifié. """
        if not self or not self._has_external_recipients(recipients_group.get('recipients', [])):
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
                'has_button_access': recipients_group.get('has_button_access')
                and email_layout_xmlid not in (False, 'mail.mail_notification_layout'),
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
        if self._has_external_recipients(recipient_ids):
            values.pop('attachment_ids', None)
        return values
