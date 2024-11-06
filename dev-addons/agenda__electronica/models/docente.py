from odoo import models, fields, api

class Docente(models.Model):
    _name = 'agenda.docente'
    _description = 'Docente'

    name = fields.Char(string='Nombre', required=True)
    ci = fields.Char(string='Cédula de Identidad', required=True)
    telefono = fields.Char(string='Teléfono', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade', required=True)
    email = fields.Char(string='Email', compute='_compute_email', inverse='_set_email', store=False)
    password = fields.Char(string='Password', store=False)

    materia_ids = fields.Many2many('materias.materia', string="Materias")
    curso_ids = fields.Many2many('agenda.curso', string="Cursos")

    @api.depends('user_id')
    def _compute_email(self):
        for record in self:
            record.email = record.user_id.partner_id.email if record.user_id else ''

    def _set_email(self):
        pass

    @api.model
    def create(self, vals):
        # Crear el usuario asociado
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
        record = super(Docente, self).create(vals)

        # Crear registros en docente_materia y curso_docente_materia
        record._crear_docente_materia()
        record._crear_curso_docente_materia()
        return record

    def write(self, vals):
        result = super(Docente, self).write(vals)
        self._crear_docente_materia()
        self._crear_curso_docente_materia()
        return result

    def _crear_docente_materia(self):
        docente_materia_obj = self.env['agenda.docente_materia']
        # Limpiar asignaciones previas
        docente_materia_obj.search([('id_docente', '=', self.id)]).unlink()
        
        # Crear nuevas asignaciones de docente a materia
        for materia in self.materia_ids:
            docente_materia_obj.create({
                'id_docente': self.id,
                'id_materia': materia.id,
            })

    def _crear_curso_docente_materia(self):
        curso_docente_materia_obj = self.env['agenda.curso_docente_materia']
        docente_materia_ids = self.env['agenda.docente_materia'].search([('id_docente', '=', self.id)])
        
        # Limpiar asignaciones previas
        curso_docente_materia_obj.search([('id_docente_materia', 'in', docente_materia_ids.ids)]).unlink()
        
        # Crear nuevas asignaciones de curso a docente_materia
        for docente_materia in docente_materia_ids:
            for curso in self.curso_ids:
                curso_docente_materia_obj.create({
                    'id_docente_materia': docente_materia.id,
                    'id_curso': curso.id,
                })


    def action_guardar_y_volver(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Docentes',
            'res_model': 'agenda.docente',
            'view_mode': 'list',
            'target': 'current',
        }
    
    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Docente',
            'res_model': 'agenda.docente',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
