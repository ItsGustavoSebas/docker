from odoo import models, fields

class DesafioEstudiante(models.Model):
    _name = 'agenda.desafio_estudiante'  # Nombre corregido
    _description = 'Relación entre Desafío y Estudiante con Puntaje'
    
    desafio_id = fields.Many2one('agenda.desafio', string='Desafío', required=True, ondelete='cascade')
    estudiante_id = fields.Many2one('agenda.estudiante', string='Estudiante', required=True, ondelete='cascade')
    puntaje = fields.Float(string='Puntaje', required=True, default=0.0)
