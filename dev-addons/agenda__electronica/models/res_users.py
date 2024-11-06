from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    device_token = fields.Char(string="Firebase Device Token")
