from odoo import models, fields

class UsuarioComunicado(models.Model):
    _name = 'agenda.usuario_comunicado'
    _description = 'Relación entre Usuario y Comunicado'

    usuario_id = fields.Many2one(
        'res.users', 
        string='Usuario', 
        required=True, 
        ondelete='cascade'
    )

    comunicado_id = fields.Many2one(
        'agenda.comunicado', 
        string='Comunicado', 
        required=True, 
        ondelete='cascade'
    )

    leido = fields.Boolean(string='Leído', default=False)
    enviado = fields.Boolean(string='Enviado', default=False)
