from odoo import models, fields, api

class PadreFamilia(models.Model):
    _name = 'agenda.padre_familia'
    _description = 'Padre de Familia'

    name = fields.Char(string='Nombre', required=True)
    ci = fields.Char(string='Cédula de Identidad', required=True)
    telefono = fields.Char(string='Teléfono', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade', required=True)
    
    email = fields.Char(string='Email', compute='_compute_email', inverse='_set_email', store=False)
    password = fields.Char(string='Password', store=False)

    estudiante_ids = fields.Many2many('agenda.estudiante', 'padre_estudiante_rel', 'padre_id', 'estudiante_id', string='Estudiantes')

    @api.depends('user_id')
    def _compute_email(self):
        for record in self:
            record.email = record.user_id.partner_id.email if record.user_id else ''

    def _set_email(self):
        # No se almacena el email en este modelo directamente
        pass

    @api.model
    def create(self, vals):
        # Creación del partner y del usuario usando los valores de email y password
        partner_vals = {
            'name': vals.get('name'),
            'email': vals.get('email'),
            'phone': vals.get('telefono'),
        }
        new_partner = self.env['res.partner'].create(partner_vals)

        user_vals = {
            'partner_id': new_partner.id,
            'login': vals.pop('email'),
            'password': vals.pop('password'),
        }
        new_user = self.env['res.users'].create(user_vals)

        vals['user_id'] = new_user.id
        record = super(PadreFamilia, self).create(vals)
        return record

    def action_guardar_y_volver(self):
        """Guardar el padre de familia y volver a la vista de lista."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Padres de Familia',
            'res_model': 'agenda.padre_familia',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        """Abrir el formulario para editar el padre de familia."""
        self.ensure_one()  
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Padre de Familia',
            'res_model': 'agenda.padre_familia', 
            'view_mode': 'form',
            'res_id': self.id, 
            'target': 'current', 
            'context': {'hide_buttons': True}, 
        }
