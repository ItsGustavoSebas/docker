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

            group_user = self.env.ref('base.group_system')  
            new_user.write({'groups_id': [(4, group_user.id)]})

            vals['user_id'] = new_user.id
            admin_role = self.env['roles.role'].search([('name', '=ilike', 'admin%')], limit=1)
            if admin_role:
                admin_role.user_ids = [(4, new_user.id)]   

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


    def create_default_administrativos(self):
        """Crear administrativos predeterminados si no existen o asignar rol si es 'Mitchell Admin' una sola vez."""
        default_administrativos = [
            {'name': 'Administrativo 1', 'cargo': 'Secretario', 'email': 'admin1@gmail.com', 'password': '12345678'},
            {'name': 'Administrativo 2', 'cargo': 'Contador', 'email': 'admin2@gmail.com', 'password': '12345678'},
            {'name': 'Administrativo 4444', 'cargo': 'Contador', 'email': 'admin4444@gmail.com', 'password': '12345678'},
        ]

        # Verificar si el usuario "Mitchell Admin" está disponible para asignarse
        mitchell_user = self.env['res.users'].search([('name', '=', 'Mitchell Admin')], limit=1)
        mitchell_assigned = self.env['agenda.administrativo'].search([('user_id', '=', mitchell_user.id)], limit=1) if mitchell_user else None

        for admin_data in default_administrativos:
            # Verificar si el administrativo ya existe para evitar duplicados
            existing_admin = self.env['agenda.administrativo'].search([('name', '=', admin_data['name'])], limit=1)
            if not existing_admin:
                if mitchell_user and not mitchell_assigned:
                    # Asignar "Mitchell Admin" solo una vez si aún no está asignado
                    admin_data.update({
                        'user_id': mitchell_user.id,
                    })
                    mitchell_assigned = True  # Marcar como asignado para evitar futuras asignaciones
                else:
                    # Verificar si el usuario con el login ya existe
                    existing_user = self.env['res.users'].search([('login', '=', admin_data['email'])], limit=1)
                    if not existing_user:
                        # Crear el `res.partner` y el `res.users` solo si no existen
                        partner_vals = {
                            'name': admin_data['name'],
                            'email': admin_data['email'],
                        }
                        new_partner = self.env['res.partner'].create(partner_vals)

                        user_vals = {
                            'partner_id': new_partner.id,
                            'login': admin_data['email'],
                            'password': admin_data['password'],
                        }
                        new_user = self.env['res.users'].create(user_vals)
                    else:
                        new_user = existing_user

                    # Asignar `user_id` al administrativo
                    admin_data.update({
                        'user_id': new_user.id,
                    })

                # Crear el administrativo con el usuario asignado o existente
                self.create(admin_data)