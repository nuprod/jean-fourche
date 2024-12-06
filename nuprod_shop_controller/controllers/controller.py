from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class CustomWebsiteShop(WebsiteSale):

    @http.route(['/shop'], type='http', auth="user", website=True)
    def shop(self, **post):
        # Vérifier si l'utilisateur est connecté
        if not request.env.user or request.env.user._is_public():
            # Rediriger vers la page de connexion ou une page d'erreur
            return request.redirect('/web/login')
        
        # Si l'utilisateur est connecté, continuer avec le comportement normal
        return super(CustomWebsiteShop, self).shop(**post)
