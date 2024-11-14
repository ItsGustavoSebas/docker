from odoo import models, fields

class Categoria(models.Model):
    _name = 'agenda.categoria'
    _description = 'categoria'

    nombre = fields.Char(string='Nombre', required=True)
    preguntas_ids = fields.One2many('agenda.pregunta', 'categoria_id', string='Desafíos')



    def create_default_categories(self):
        """Crear categorías predeterminadas si no existen."""
        default_categories = ['Fisica', 'Matematica', 'Filosofia']

        for category_name in default_categories:
            # Verificar si la categoría ya existe para evitar duplicados
            existing_category = self.env['agenda.categoria'].search([('nombre', '=', category_name)], limit=1)
            if not existing_category:
                self.env['agenda.categoria'].create({'nombre': category_name})