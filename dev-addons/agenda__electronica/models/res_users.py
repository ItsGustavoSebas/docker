from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    device_token_ids = fields.One2many('user.device.token', 'user_id', string="Device Tokens")
