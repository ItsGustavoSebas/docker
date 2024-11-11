from odoo import models, fields

class Pregunta(models.Model):
    _name = 'agenda.pregunta'
    _description = 'Modelo de Pregunta'

    texto = fields.Char(string='Texto de la Pregunta', required=True)
    desafio_id = fields.Many2one('agenda.desafio', string='Desafío', required=True)
    categoria_id = fields.Many2one('agenda.categoria', string='Categoría', required=True)
    opciones_ids = fields.One2many('agenda.opciones', 'pregunta_id', string='Opciones')
