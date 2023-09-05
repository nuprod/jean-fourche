# -*- coding: utf-8 -*-
# from odoo import http


# class NuprodTemplateModule(http.Controller):
#     @http.route('/nuprod_template_module/nuprod_template_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nuprod_template_module/nuprod_template_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('nuprod_template_module.listing', {
#             'root': '/nuprod_template_module/nuprod_template_module',
#             'objects': http.request.env['nuprod_template_module.nuprod_template_module'].search([]),
#         })

#     @http.route('/nuprod_template_module/nuprod_template_module/objects/<model("nuprod_template_module.nuprod_template_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nuprod_template_module.object', {
#             'object': obj
#         })