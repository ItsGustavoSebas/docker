from odoo import models, fields, api

class Administrativo(models.Model):
    _name = 'agenda.administrativo'
    _description = 'Administrativo'

    name = fields.Char(string='Nombre', required=True)
    cargo = fields.Char(string='Cargo', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade', required=True)
    
    email = fields.Char(string='Email', compute='_compute_email', inverse='_set_email', store=False)
    password = fields.Char(string='Password', store=False)

    @api.depends('user_id')
    def _compute_email(self):
        for record in self:
            record.email = record.user_id.partner_id.email if record.user_id else ''

    def _set_email(self):
        pass

    @api.model
    def create(self, vals):
        if not vals.get('user_id'):
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

        record = super(Administrativo, self).create(vals)
        return record

    def action_guardar_y_volver(self):
        """Guardar el administrativo y volver a la vista de lista."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Administrativos',
            'res_model': 'agenda.administrativo',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        """Abrir el formulario para editar el administrativo."""
        self.ensure_one()  
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Administrativo',
            'res_model': 'agenda.administrativo', 
            'view_mode': 'form',
            'res_id': self.id, 
            'target': 'current', 
            'context': {'hide_buttons': True}, 
        }
