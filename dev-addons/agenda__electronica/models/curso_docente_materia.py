from odoo import models, fields, api

class CursoDocenteMateria(models.Model):
    _name = 'agenda.curso_docente_materia'
    _description = 'Asignación de Curso, Docente y Materia'
    _rec_name = 'name'

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

    name = fields.Char(
        string='Nombre', 
        compute='_compute_name', 
        store=True
    )

    @api.depends('id_curso.display_name', 'id_docente_materia.id_materia.name')
    def _compute_name(self):
        for record in self:
            curso = record.id_curso.display_name or 'Curso desconocido'
            materia = record.id_docente_materia.id_materia.name or 'Materia desconocida'
            record.name = f"{curso} - {materia}"
