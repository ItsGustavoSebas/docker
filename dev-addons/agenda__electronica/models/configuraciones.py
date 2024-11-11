from odoo import models, fields, api

class Configuraciones(models.Model):
    _name = 'agenda.configuraciones'
    _description = 'Configuraciones'

    puntos = fields.Integer(string='Puntos', required=True, help="Puntos asignados en la configuración.")
    frecuencia = fields.Integer(string='Frecuencia', required=True, help="Frecuencia de desafio configurada en el sistema.")

    @api.model
    def init(self):
        if not self.search([], limit=1):
            self.create({
                'puntos': 5,
                'frecuencia': 7,
            })
