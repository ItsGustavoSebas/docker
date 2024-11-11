from odoo import models, fields

class UsuarioActividad(models.Model):
    _name = 'agenda.usuario_actividad'
    _description = 'Relación entre Usuario y actividad'

    usuario_id = fields.Many2one(
        'res.users', 
        string='Usuario', 
        required=True, 
        ondelete='cascade'
    )

    actividad_id = fields.Many2one(
        'agenda.actividad', 
        string='actividad', 
        required=True, 
        ondelete='cascade'
    )

    leido = fields.Boolean(string='Leído', default=False)
    enviado = fields.Boolean(string='Enviado', default=False)
