{
    'name': 'Aldais - Notification générique des tickets SAV',
    'summary': 'Les mails envoyés aux clients sur un ticket d\'assistance ne contiennent plus la réponse',
    'description': """
        Remplace le contenu des mails de notification envoyés aux clients (contacts externes)
        sur un ticket d'assistance par un message générique invitant à consulter le ticket
        sur le portail, afin que les réponses clients restent centralisées dans le ticket.
        Le ticket, le portail et les mails envoyés aux utilisateurs internes ne changent pas.
    """,
    'author': 'Aldais',
    'category': 'Custom',
    'version': '17.0.1.0.0',
    'depends': ['helpdesk', 'mail'],
    'data': [
        'data/mail_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
