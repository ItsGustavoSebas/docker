from odoo import models, fields, api

class Materia(models.Model):
    _name = 'materias.materia'
    _description = 'Materia'

    name = fields.Char(string='Nombre', required=True)

    @api.model
    def create(self, vals):
        """Crear un nuevo registro de Materia."""
        record = super(Materia, self).create(vals)
        return record

    def write(self, vals):
        """Editar un registro de Materia existente."""
        result = super(Materia, self).write(vals)
        return result

    def action_guardar_y_volver(self):
        """Guardar y volver a la vista de lista de Materias."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Materias',
            'res_model': 'materias.materia',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        """Abrir el formulario de Materia para editar."""
        self.ensure_one()  
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Materia',
            'res_model': 'materias.materia', 
            'view_mode': 'form',
            'res_id': self.id, 
            'target': 'current', 
            'context': {'hide_buttons': True},
        }


    def create_default_materias(self):
        """Crear materias predeterminadas si no existen."""
        default_materias = ['Matemáticas', 'Lenguaje', 'Ciencias', 'Historia', 'Geografía']

        for materia_name in default_materias:
            # Verificar si la materia ya existe para evitar duplicados
            existing_materia = self.env['materias.materia'].search([('name', '=', materia_name)], limit=1)
            if not existing_materia:
                self.create({'name': materia_name})                