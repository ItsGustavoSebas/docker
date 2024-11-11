from odoo import models, fields, api

class SolicitudDesafio(models.Model):
    _name = 'agenda.solicitud_desafio'
    _description = 'Solicitud de Desafío entre Estudiantes'

    desafiante_id = fields.Many2one('agenda.estudiante', string='Estudiante Desafiante', required=True, ondelete='cascade')
    desafiado_id = fields.Many2one('agenda.estudiante', string='Estudiante Desafiado', required=True, ondelete='cascade')
    is_aceptado = fields.Boolean(string='Aceptado', default=False)
    fecha_solicitud = fields.Datetime(string='Fecha de Solicitud', default=fields.Datetime.now)
    mensaje = fields.Char(string='Mensaje', required=True, default="¡Te desafio!")

    @api.model
    def create(self, vals):
        if 'desafiante_id' in vals and 'desafiado_id' in vals:
            existe_solicitud = self.search([
                ('desafiante_id', '=', vals['desafiante_id']),
                ('desafiado_id', '=', vals['desafiado_id']),
                ('is_aceptado', '=', False)
            ])
            if existe_solicitud:
                raise ValueError("Ya existe una solicitud pendiente entre estos estudiantes.")

        # Crear la solicitud
        return super(SolicitudDesafio, self).create(vals)
