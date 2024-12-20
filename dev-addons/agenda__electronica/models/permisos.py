from odoo import models, fields

class Permiso(models.Model):
    _name = 'permisos.permiso'
    _description = 'Permiso'

    name = fields.Char(string='Nombre del Permiso', required=True)

    # role_ids = fields.Many2many(
    #     'roles.role',  # Relación con el modelo 'roles.role'
    #     'role_permiso_rel',  # Tabla intermedia
    #     'permiso_id',  # ID del permiso
    #     'role_id',  # ID del rol
    #     string='Roles'
    # )

    def action_open_form(self):
        """Abrir el formulario para editar el permiso."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Permiso',
            'res_model': 'permisos.permiso',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',  # Redirige sin abrir modal
            'context': {'hide_buttons': True},
        }

    def action_guardar_y_volver(self):
        """Guardar el permiso y volver a la lista."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Permisos',
            'res_model': 'permisos.permiso',
            'view_mode': 'list',
            'target': 'current',  # Redirige sin abrir modal
        }



    def create_default_permissions(self):
        """Crear permisos predeterminados si no existen."""
        default_permissions = ['Permiso 1', 'Permiso 2', 'Permiso 3']

        for permission_name in default_permissions:
            # Verificar si el permiso ya existe para evitar duplicados
            existing_permission = self.env['permisos.permiso'].search([('name', '=', permission_name)], limit=1)
            if not existing_permission:
                self.env['permisos.permiso'].create({'name': permission_name})