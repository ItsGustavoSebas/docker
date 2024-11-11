from odoo import models, fields

class Opciones(models.Model):
    _name = 'agenda.opciones'
    _description = 'pregunta'

    opcion = fields.Char(string='Opción de Respuesta', required=True)
    is_correct = fields.Boolean(string='Es Correcta', default=False)
    pregunta_id = fields.Many2one('agenda.pregunta', string='Pregunta', required=True)

    estudiantes_ids = fields.One2many(
        'agenda.estudiante_opciones',  # Nombre de la tabla intermedia corregido
        'opcion_id',
        string='Estudiantes que Seleccionaron'
    )
