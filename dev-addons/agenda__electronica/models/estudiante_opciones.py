from odoo import models, fields

class EstudianteOpciones(models.Model):
    _name = 'agenda.estudiante_opciones'  # Nombre corregido
    _description = 'Relación de Opciones Seleccionadas por Estudiantes'

    estudiante_id = fields.Many2one('agenda.estudiante', string='Estudiante', required=True, ondelete='cascade')
    opcion_id = fields.Many2one('agenda.opciones', string='Opción Seleccionada', required=True, ondelete='cascade')
