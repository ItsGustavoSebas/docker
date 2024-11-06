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
            else:
                for user in role.user_ids:
                    admin_count = self.env['res.users'].search_count([
                        ('groups_id', 'in', [admin_group.id])
                    ])
                    
                    if admin_count <= 1:
                        raise ValueError("No puedes eliminar el último administrador del sistema.")
                    
                    if admin_group in user.groups_id:
                        user.groups_id = [(3, admin_group.id)]

    def init(self):
        """Crear roles predeterminados si no existen."""
        default_roles = ['Administradores', 'Docentes', 'Padres', 'Estudiantes']

        for role_name in default_roles:
            # Verificar si el rol ya existe para evitar duplicados
            existing_role = self.env['roles.role'].search([('name', '=', role_name)], limit=1)
            if not existing_role:
                self.env['roles.role'].create({'name': role_name})
