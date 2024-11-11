from odoo import models, fields

class Categoria(models.Model):
    _name = 'agenda.categoria'
    _description = 'categoria'

    nombre = fields.Char(string='Nombre', required=True)
    preguntas_ids = fields.One2many('agenda.pregunta', 'categoria_id', string='Desafíos')
