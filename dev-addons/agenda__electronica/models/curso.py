from odoo import models, fields, api, _
import csv
import base64
from io import StringIO

class Curso(models.Model):
    _name = 'agenda.curso'
    _description = 'Curso'

    curso = fields.Integer(string='Curso', required=True, default=1)
    paralelo = fields.Char(string='Paralelo', required=True, default='')
    display_name = fields.Char(string='Curso', compute='_compute_display_name', store=True)
    estudiante_ids = fields.One2many('agenda.estudiante', 'curso_id', string='Estudiantes')

    curso_docente_materia_ids = fields.One2many(
        'agenda.curso_docente_materia',  # Modelo relacionado
        'id_curso',                      # Campo inverso en el modelo relacionado
        string='Docentes y Materias'
    )

    csv_file = fields.Binary(string="Archivo CSV")
    csv_filename = fields.Char(string="Nombre del Archivo CSV")

    @api.depends('curso', 'paralelo')
    def _compute_display_name(self):
        for record in self:
            if record.curso and record.paralelo: 
                record.display_name = f'{record.curso}"{record.paralelo}"'
            else:
                record.display_name = ''

    def importar_estudiantes_y_padres(self):
        """ Importa datos de estudiantes y padres desde un archivo CSV """
        if not self.csv_file:
            raise ValueError(_("Debe seleccionar un archivo CSV para importar."))

        file_content = base64.b64decode(self.csv_file).decode('utf-8')
        reader = csv.DictReader(StringIO(file_content))
        
        for row in reader:
            estudiante_ci = row['CI del Estudiante']
            curso_id = self.id

            # 1. Buscar o crear estudiante
            estudiante = self.env['agenda.estudiante'].search([('ci', '=', estudiante_ci)], limit=1)
            if estudiante:
                if estudiante.curso_id.id != curso_id:
                    estudiante.curso_id = curso_id
            else:
                estudiante = self.env['agenda.estudiante'].create({
                    'name': row['Nombre del Estudiante'],
                    'ci': estudiante_ci,
                    'password': estudiante_ci,
                    'email': row['Email del Estudiante'],
                    'curso_id': curso_id,
                })

            # 2. Procesar los padres (padre, madre, tutor)
            self._procesar_padre_familia(row, estudiante, 'l Padre')
            self._procesar_padre_familia(row, estudiante, ' la Madre')
            self._procesar_padre_familia(row, estudiante, 'l Tutor')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cursos',
            'res_model': 'agenda.curso',
            'view_mode': 'list',
            'target': 'current',
        }

    def _procesar_padre_familia(self, row, estudiante, tipo_parentesco):
        """ Verifica o crea al padre de familia y lo asocia al estudiante """
        nombre = row[f'Nombre de{tipo_parentesco}']
        ci = row[f'CI de{tipo_parentesco}']
        email = row[f'Correo de{tipo_parentesco}']
        telefono = row.get(f'Teléfono de{tipo_parentesco}')

        if not ci:
            return  # Ignorar si no hay CI

        # Buscar o crear padre de familia
        padre_familia = self.env['agenda.padre_familia'].search([('ci', '=', ci)], limit=1)
        if padre_familia:
            # Si el padre ya existe, solo agregar la relación si no está
            if estudiante not in padre_familia.estudiante_ids:
                padre_familia.estudiante_ids = [(4, estudiante.id)]
        else:
            # Crear nuevo padre de familia y asociar al estudiante
            padre_familia = self.env['agenda.padre_familia'].create({
                'name': nombre,
                'ci': ci,
                'password': ci,
                'telefono': telefono,
                'email': email,
                'estudiante_ids': [(4, estudiante.id)],
            })


    @api.model
    def create(self, vals):
        record = super(Curso, self).create(vals)
        return record

    def write(self, vals):
        result = super(Curso, self).write(vals)
        return result

    def action_guardar_y_volver(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cursos',
            'res_model': 'agenda.curso',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Curso',
            'res_model': 'agenda.curso',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'hide_buttons': True},
        }
