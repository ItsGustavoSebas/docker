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
        padre_role = self.env['roles.role'].search([('name', '=ilike', 'padr%')], limit=1)
        if padre_role:
            padre_role.user_ids = [(4, new_user.id)]
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


    def create_default_padres_familia(self):
        """Crear padres de familia predeterminados si no existen."""
        default_padres = [
            {'name': 'Padre 1', 'ci': '123456', 'telefono': '555-1234', 'email': 'padre12@gmail.com', 'password': '12345678', 'estudiante_cis': ['123456', '654321']},
            {'name': 'Padre 2', 'ci': '654321', 'telefono': '555-5678', 'email': 'padre22@gmail.com', 'password': '12345678', 'estudiante_cis': ['654322']},
        ]

        for padre_data in default_padres:
            # Verificar si el padre ya existe para evitar duplicados
            existing_padre = self.env['agenda.padre_familia'].search([('ci', '=', padre_data['ci'])], limit=1)
            if not existing_padre:
                # Verificar si el usuario con el login ya existe
                existing_user = self.env['res.users'].search([('login', '=', padre_data['email'])], limit=1)
                if not existing_user:
                    # Crear el `res.partner` y el `res.users` solo si no existen
                    partner_vals = {
                        'name': padre_data['name'],
                        'email': padre_data['email'],
                    }
                    new_partner = self.env['res.partner'].create(partner_vals)

                    user_vals = {
                        'partner_id': new_partner.id,
                        'login': padre_data['email'],
                        'password': padre_data['password'],
                    }
                    new_user = self.env['res.users'].create(user_vals)
                else:
                    new_user = existing_user

                # Obtener IDs de estudiantes en base a la lista de cédulas proporcionadas
                estudiante_ids = self.env['agenda.estudiante'].search([('ci', 'in', padre_data.pop('estudiante_cis'))]).ids

                # Asignar `user_id` y `estudiante_ids` al padre y crear el registro sin duplicar `res.users`
                padre_data.update({
                    'user_id': new_user.id,
                    'estudiante_ids': [(6, 0, estudiante_ids)],
                })
                # Crear el padre de familia sin duplicar la creación del usuario
                super(PadreFamilia, self).create(padre_data)