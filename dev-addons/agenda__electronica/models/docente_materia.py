from odoo import models, fields

class DocenteMateria(models.Model):
    _name = 'agenda.docente_materia'
    _description = 'Asignación de Docente a Materia'

    id_docente = fields.Many2one('agenda.docente', string='Docente', required=True, ondelete='cascade')
    id_materia = fields.Many2one('materias.materia', string='Materia', required=True, ondelete='cascade')
