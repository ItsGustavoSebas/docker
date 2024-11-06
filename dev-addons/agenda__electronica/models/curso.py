from odoo import models, fields, api

class Curso(models.Model):
    _name = 'agenda.curso'
    _description = 'Curso'

    curso = fields.Integer(string='Curso', required=True, default=1)
    paralelo = fields.Char(string='Paralelo', required=True, default='')
    display_name = fields.Char(string='Curso', compute='_compute_display_name', store=True)
    estudiante_ids = fields.One2many('agenda.estudiante', 'curso_id', string='Estudiantes')

    @api.depends('curso', 'paralelo')
    def _compute_display_name(self):
        for record in self:
            if record.curso and record.paralelo: 
                record.display_name = f'{record.curso}"{record.paralelo}"'
            else:
                record.display_name = ''  # Campo vacío si no hay valores válidos

    @api.model
    def create(self, vals):
        record = super(Curso, self).create(vals)
        return record

    def write(self, vals):
        result = super(Curso, self).write(vals)
        return result

    def action_guardar_y_volver(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cursos',
            'res_model': 'agenda.curso',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Curso',
            'res_model': 'agenda.curso',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'hide_buttons': True},
        }
