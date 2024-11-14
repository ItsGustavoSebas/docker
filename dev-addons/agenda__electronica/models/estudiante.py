from odoo import models, fields, api

class Estudiante(models.Model):
    _name = 'agenda.estudiante'
    _description = 'Estudiante'

    name = fields.Char(string='Nombre', required=True)
    ci = fields.Char(string='Cédula de Identidad', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', ondelete='cascade', required=True)
    curso_id = fields.Many2one('agenda.curso', string='Curso', required=True, ondelete='cascade')
    
    email = fields.Char(string='Email', compute='_compute_email', inverse='_set_email', store=False)
    password = fields.Char(string='Password', store=False)

    padre_familia_ids = fields.Many2many(
        'agenda.padre_familia',
        'padre_estudiante_rel',  
        'estudiante_id',         
        'padre_id',             
        string='Padres de Familia'
    )

    desafio_ids = fields.One2many(
        'agenda.desafio_estudiante',  
        'estudiante_id', 
        string='Desafíos Participados'
    )



    opciones_ids = fields.One2many(
        'agenda.estudiante_opciones',  
        'estudiante_id',
        string='Opciones Seleccionadas'
    )

    

    @api.depends('user_id')
    def _compute_email(self):
        for record in self:
            record.email = record.user_id.partner_id.email if record.user_id else ''

    def _set_email(self):
        pass

    @api.model
    def create(self, vals):
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
        record = super(Estudiante, self).create(vals)
        estudiante_role = self.env['roles.role'].search([('name', '=ilike', 'estud%')], limit=1)
        if estudiante_role:
            estudiante_role.user_ids = [(4, new_user.id)]

        return record

    def action_guardar_y_volver(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Estudiantes',
            'res_model': 'agenda.estudiante',
            'view_mode': 'list',
            'target': 'current',
        }
    
    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Estudiante',
            'res_model': 'agenda.estudiante',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }




    def create_default_students(self):
        """Crear estudiantes predeterminados si no existen."""
        default_students = [
            {'name': 'Estudiante 1', 'ci': '123456', 'email': 'estudiante11@gmail.com', 'password': '12345678', 'curso_name': 1},
            {'name': 'Estudiante 2', 'ci': '654321', 'email': 'estudiante22@gmail.com', 'password': '12345678', 'curso_name': 1},
            {'name': 'Estudiante 3', 'ci': '654322', 'email': 'estudiante33@gmail.com', 'password': '12345678', 'curso_name': 1},
            {'name': 'Estudiante 4', 'ci': '654323', 'email': 'estudiante44@gmail.com', 'password': '12345678', 'curso_name': 2},
            {'name': 'Estudiante 5', 'ci': '654324', 'email': 'estudiante55@gmail.com', 'password': '12345678', 'curso_name': 3},
        ]
        
        for student_data in default_students:
            # Verificar si el estudiante ya existe para evitar duplicados
            existing_student = self.env['agenda.estudiante'].search([('ci', '=', student_data['ci'])], limit=1)
            if not existing_student:
                # Verificar si el usuario con el login ya existe
                existing_user = self.env['res.users'].search([('login', '=', student_data['email'])], limit=1)
                if not existing_user:
                    # Crear el `res.partner` y el `res.users` solo si no existen
                    partner_vals = {
                        'name': student_data['name'],
                        'email': student_data['email'],
                    }
                    new_partner = self.env['res.partner'].create(partner_vals)
    
                    user_vals = {
                        'partner_id': new_partner.id,
                        'login': student_data['email'],
                        'password': student_data['password'],
                    }
                    new_user = self.env['res.users'].create(user_vals)
                else:
                    new_user = existing_user
                
                # Buscar el curso correspondiente
                curso = self.env['agenda.curso'].search([('curso', '=', student_data.pop('curso_name'))], limit=1)
                if curso:
                    # Asignar `user_id` y `curso_id` al estudiante y crear el registro sin crear nuevo `res.users`
                    student_data.update({
                        'user_id': new_user.id,
                        'curso_id': curso.id,
                    })
                    # Crear el estudiante sin duplicar la creación del usuario
                    super(Estudiante, self).create(student_data)
    