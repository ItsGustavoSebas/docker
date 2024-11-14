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
            'phone': vals.get('telefono'),
        }
        new_partner = self.env['res.partner'].create(partner_vals)

        user_vals = {
            'partner_id': new_partner.id,
            'login': vals.pop('email'),
            'password': vals.pop('password'),
        }
        new_user = self.env['res.users'].create(user_vals)

        group_user = self.env.ref('base.group_user')  
        new_user.write({'groups_id': [(4, group_user.id)]})

        vals['user_id'] = new_user.id
        record = super(Docente, self).create(vals)

        # Crear registros en docente_materia y curso_docente_materia
        record._crear_docente_materia()
        record._crear_curso_docente_materia()
        docente_role = self.env['roles.role'].search([('name', '=ilike', 'docen%')], limit=1)
        if docente_role:
            docente_role.user_ids = [(4, new_user.id)]
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



    def create_default_docentes(self):
        """Crear docentes predeterminados si no existen."""
        default_docentes = [
            {'name': 'Docente 1', 'ci': '123456', 'telefono': '555-1234', 'email': 'docente11@gmail.com', 'password': 'password1', 'materia_names': ['Matemáticas'], 'curso_nums': [1]},
            {'name': 'Docente 2', 'ci': '654321', 'telefono': '555-5678', 'email': 'docente22@gmail.com', 'password': 'password2', 'materia_names': ['Lenguaje'], 'curso_nums': [2]},
        ]

        for docente_data in default_docentes:
            # Verificar si el docente ya existe para evitar duplicados
            existing_docente = self.env['agenda.docente'].search([('ci', '=', docente_data['ci'])], limit=1)
            if not existing_docente:
                # Verificar si el usuario con el login ya existe
                existing_user = self.env['res.users'].search([('login', '=', docente_data['email'])], limit=1)
                if not existing_user:
                    # Crear el `res.partner` y el `res.users` solo si no existen
                    partner_vals = {
                        'name': docente_data['name'],
                        'email': docente_data['email'],
                    }
                    new_partner = self.env['res.partner'].create(partner_vals)

                    user_vals = {
                        'partner_id': new_partner.id,
                        'login': docente_data['email'],
                        'password': docente_data['password'],
                    }
                    new_user = self.env['res.users'].create(user_vals)
                else:
                    new_user = existing_user

                # Obtener IDs de materias y cursos
                materia_ids = self.env['materias.materia'].search([('name', 'in', docente_data.pop('materia_names'))]).ids
                curso_ids = self.env['agenda.curso'].search([('curso', 'in', docente_data.pop('curso_nums'))]).ids

                # Asignar `user_id`, `materia_ids`, y `curso_ids` al docente y crear el registro sin duplicar `res.users`
                docente_data.update({
                    'user_id': new_user.id,
                    'materia_ids': [(6, 0, materia_ids)],
                    'curso_ids': [(6, 0, curso_ids)],
                })
                # Crear el docente sin duplicar la creación del usuario
                super(Docente, self).create(docente_data)