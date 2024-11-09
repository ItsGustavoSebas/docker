from odoo import models, fields, api

class EventoEstudianteRel(models.Model):
    _name = 'agenda.evento_estudiante'
    _description = 'Relación entre Evento y Estudiante'

    evento_id = fields.Many2one('agenda.evento', string="Evento", required=True, ondelete='cascade')
    estudiante_id = fields.Many2one('agenda.estudiante', string="Estudiante", required=True, ondelete='cascade')

    leido = fields.Boolean(string="Leído", default=False)
    confirmacion = fields.Boolean(string="Confirmación", default=False)
    asistencia = fields.Boolean(string="Asistió", default=False)