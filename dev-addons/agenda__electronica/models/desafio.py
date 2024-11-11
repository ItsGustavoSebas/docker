from odoo import models, fields

class Desafio(models.Model):
    _name = 'agenda.desafio'
    _description = 'Desafío'

    tema = fields.Char(string='Tema', required=True)


    estudiantes_ids = fields.One2many(
        'agenda.desafio_estudiante', 
        'desafio_id', 
        string='Estudiantes Participantes'
    )