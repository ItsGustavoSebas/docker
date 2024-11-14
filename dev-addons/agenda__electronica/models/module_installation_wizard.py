# module_installation_wizard.py
from odoo import api, fields, models

class ModuleInstallationWizard(models.TransientModel):
    _name = 'module.installation.wizard'
    _description = 'Module Installation Wizard'

    load_seeders = fields.Boolean("¿Desea cargar datos de ejemplo?")

    def action_apply(self):
        """Lógica para el botón 'Aplicar' en el wizard."""
        if self.load_seeders:
            # Llamar a los métodos de creación de datos predeterminados
            self.env['agenda.categoria'].create_default_categories()
            self.env['permisos.permiso'].create_default_permissions()
            self.env['agenda.curso'].create_default_courses()
            self.env['agenda.estudiante'].create_default_students()
            self.env['materias.materia'].create_default_materias()
            self.env['agenda.docente'].create_default_docentes()
            self.env['agenda.padre_familia'].create_default_padres_familia() 
            self.env['agenda.administrativo'].create_default_administrativos() 
            self.env['roles.role'].create_default_roles()
        return {'type': 'ir.actions.act_window_close'}
