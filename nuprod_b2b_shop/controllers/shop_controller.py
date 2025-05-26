from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class CustomWebsiteShop(WebsiteSale):

    @http.route(['/shop', '/', '/shop/', '/shop/<path:path>'], type='http', auth="user", website=True)
    def shop(self, **post):
        # Vérifier si l'utilisateur est connecté
        if not request.env.user or request.env.user._is_public():
            # Si l'utilisateur n'est pas connecté ou est un visiteur public, rediriger vers la page de connexion
            return request.redirect('/web/login')
        
        # Si l'utilisateur est connecté, continuer normalement avec le comportement de la route /shop
        return super(CustomWebsiteShop, self).shop(**post)
