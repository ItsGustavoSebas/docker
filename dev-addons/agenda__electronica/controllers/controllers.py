# -*- coding: utf-8 -*-
# from odoo import http


# class AgendaElectronica(http.Controller):
#     @http.route('/agenda__electronica/agenda__electronica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/agenda__electronica/agenda__electronica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('agenda__electronica.listing', {
#             'root': '/agenda__electronica/agenda__electronica',
#             'objects': http.request.env['agenda__electronica.agenda__electronica'].search([]),
#         })

#     @http.route('/agenda__electronica/agenda__electronica/objects/<model("agenda__electronica.agenda__electronica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('agenda__electronica.object', {
#             'object': obj
#         })

