from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    device_token_ids = fields.One2many('user.device.token', 'user_id', string="Device Tokens")
    role_ids = fields.Many2many(
        'roles.role',         # Modelo relacionado
        'role_user_rel',       # Nombre de la tabla intermedia
        'user_id',             # Columna de usuario
        'role_id',             # Columna de rol
        string='Roles'         # Etiqueta para mostrar en la interfaz
    )