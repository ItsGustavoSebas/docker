from odoo import models, fields, api

class Estudiante(models.Model):
    _name = 'agenda.estudiante'
    _description = 'Estudiante'

    name = fields.Char(string='Nombre', required=True)
    ci = fields.Char(string='Cédula de Identidad', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade', required=True)
    curso_id = fields.Many2one('agenda.curso', string='Curso', required=True, ondelete='cascade')
    
    email = fields.Char(string='Email', compute='_compute_email', inverse='_set_email', store=False)
    password = fields.Char(string='Password', store=False)

    padre_familia_ids = fields.Many2many(
        'agenda.padre_familia',
        'padre_estudiante_rel',  
        'estudiante_id',         
        'padre_id',             
        string='Padres de Familia'
    )

    desafio_ids = fields.One2many(
        'agenda.desafio_estudiante',  
        'estudiante_id', 
        string='Desafíos Participados'
    )



    opciones_ids = fields.One2many(
        'agenda.estudiante_opciones',  
        'estudiante_id',
        string='Opciones Seleccionadas'
    )

    

    @api.depends('user_id')
    def _compute_email(self):
        for record in self:
            record.email = record.user_id.partner_id.email if record.user_id else ''

    def _set_email(self):
        pass

    @api.model
    def create(self, vals):
        partner_vals = {
            'name': vals.get('name'),
            'email': vals.get('email'),
        }
        new_partner = self.env['res.partner'].create(partner_vals)

        user_vals = {
            'partner_id': new_partner.id,
            'login': vals.pop('email'),
            'password': vals.pop('password'),
        }
        new_user = self.env['res.users'].create(user_vals)

        vals['user_id'] = new_user.id
        record = super(Estudiante, self).create(vals)
        return record

    def action_guardar_y_volver(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Estudiantes',
            'res_model': 'agenda.estudiante',
            'view_mode': 'list',
            'target': 'current',
        }
    
    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Estudiante',
            'res_model': 'agenda.estudiante',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

