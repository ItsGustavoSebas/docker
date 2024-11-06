from odoo import models, fields

class UserDeviceToken(models.Model):
    _name = 'user.device.token'
    _description = 'User Device Token'

    user_id = fields.Many2one('res.users', string="User", required=True, ondelete='cascade')
    device_token = fields.Char(string="Firebase Device Token", required=True)
