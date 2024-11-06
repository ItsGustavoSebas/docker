from odoo import models, fields

class CursoDocenteMateria(models.Model):
    _name = 'agenda.curso_docente_materia'
    _description = 'Asignación de Curso, Docente y Materia'

    id_docente_materia = fields.Many2one(
        'agenda.docente_materia', 
        string='Docente-Materia', 
        required=True, 
        ondelete='cascade'
    )
    id_curso = fields.Many2one(
        'agenda.curso', 
        string='Curso', 
        required=True, 
        ondelete='cascade'
    )
