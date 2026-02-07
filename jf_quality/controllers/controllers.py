# -*- coding: utf-8 -*-
# from odoo import http


# class JfQuality(http.Controller):
#     @http.route('/jf_quality/jf_quality', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jf_quality/jf_quality/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jf_quality.listing', {
#             'root': '/jf_quality/jf_quality',
#             'objects': http.request.env['jf_quality.jf_quality'].search([]),
#         })

#     @http.route('/jf_quality/jf_quality/objects/<model("jf_quality.jf_quality"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jf_quality.object', {
#             'object': obj
#         })

