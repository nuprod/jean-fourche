from odoo import fields, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    # les pièces jointes sont celles du mail.message (_inherits) : on ne peut
    # pas les retirer d'un seul mail, on les ignore donc à l'envoi
    send_without_attachments = fields.Boolean()

    def _prepare_outgoing_list(self, recipients_follower_status=None):
        results = super()._prepare_outgoing_list(recipients_follower_status=recipients_follower_status)
        if self.send_without_attachments:
            for email_values in results:
                email_values['attachments'] = []
        return results
