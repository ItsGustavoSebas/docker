from odoo import models, fields

class Role(models.Model):
    _name = 'roles.role'
    _description = 'Role'

    name = fields.Char(string='Role Name', required=True)

    user_ids = fields.Many2many(
        'res.users',
        'role_user_rel',
        'role_id',
        'user_id',
        string='Users'
    )

    permiso_ids = fields.Many2many(
        'permisos.permiso',
        'role_permiso_rel',
        'role_id',
        'permiso_id',
        string='Permisos'
    )

    def action_guardar_y_volver(self):
        """Guardar el rol y volver a la lista."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Roles',
            'res_model': 'roles.role',
            'view_mode': 'list',
            'target': 'current',
        }

    def open_user_assignment(self):
        """Abrir la vista de asignación de usuarios y permisos."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asignar Usuarios y Permisos',
            'res_model': 'roles.role',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'is_assignment': True},
        }


    def create(self, vals):
        role = super(Role, self).create(vals)
        role._update_admin_group()
        return role

    def write(self, vals):
        res = super(Role, self).write(vals)
        self._update_admin_group()
        return res

    def _update_admin_group(self):
        admin_group = self.env.ref('base.group_system')

        for role in self:
            is_admin_role = role.name.lower() in ['administrador', 'admin', 'administradores']
            if is_admin_role:
                # Añadir usuarios al grupo de administradores
                for user in role.user_ids:
                    if admin_group not in user.groups_id:
                        user.groups_id = [(4, admin_group.id)]


    def init(self):
        """Crear roles predeterminados si no existen."""
        default_roles = ['Administradores', 'Docentes', 'Padres', 'Estudiantes']

        for role_name in default_roles:
            # Verificar si el rol ya existe para evitar duplicados
            existing_role = self.env['roles.role'].search([('name', '=', role_name)], limit=1)
            if not existing_role:
                self.env['roles.role'].create({'name': role_name})



    def create_default_roles(self):
        """Crear roles predeterminados y asignarlos a usuarios según el prefijo del nombre."""
        default_roles = {
            'Administradores': 'admin',
            'Docentes': 'docente',
            'Padres': 'padre',
            'Estudiantes': 'estudiante'
        }

        for role_name, prefix in default_roles.items():
            # Verificar si el rol ya existe para evitar duplicados
            role = self.env['roles.role'].search([('name', '=', role_name)], limit=1)
            if not role:
                role = self.env['roles.role'].create({'name': role_name})
            
            # Asignar usuarios cuyo nombre comienza con el prefijo al rol correspondiente
            matching_users = self.env['res.users'].search([('name', '=ilike', f'{prefix}%')])
            role.user_ids = [(4, user.id) for user in matching_users]

            # Opcionalmente, asignar permisos predeterminados (si los permisos están definidos para cada rol)
            default_permissions = self.env['permisos.permiso'].search([('name', 'ilike', role_name)])
            role.permiso_ids = [(4, permiso.id) for permiso in default_permissions]