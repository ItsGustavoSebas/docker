from odoo import http
from odoo.http import request

class CursoController(http.Controller):

    @http.route('/api/cursos', auth='user', methods=['GET'], type='json', csrf=False)
    def get_cursos(self):
        cursos = request.env['agenda.curso'].sudo().search([])
        cursos_data = [{
            'id': curso.id,
            'display_name': curso.display_name,
            'curso': curso.curso,
            'paralelo': curso.paralelo
        } for curso in cursos]
        
        return {'cursos': cursos_data}



    @http.route('/api/curso_docente/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def get_cursos_docente(self, user_id):
        # Buscar el docente asociado al user_id proporcionado
        docente = request.env['agenda.docente'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar si el docente existe y obtener los cursos asociados
        if docente:
            cursos = docente.curso_ids
            materias_nombres = ', '.join([materia.name for materia in docente.materia_ids])
            cursos_data = [{
                'id': curso.id,
                'display_name': curso.display_name,
                'curso': curso.curso,
                'paralelo': curso.paralelo,
                # 'curso_materia': f"{curso.display_name} - {docente.materia_ids.id_materia.name}",
            } for curso in cursos]
            return {'cursos': cursos_data}
        else:
            return {'error': 'No se encontró un docente asociado a este usuario'}


    @http.route('/api/curso_estudiante/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def get_cursos_estudiante(self, user_id):
        # Buscar el estudiante asociado al user_id proporcionado
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar si el estudiante existe y obtener el curso asociado
        if estudiante and estudiante.curso_id:
            curso = estudiante.curso_id
            curso_data = {
                'id': curso.id,
                'display_name': curso.display_name,
                'curso': curso.curso,
                'paralelo': curso.paralelo
            }
            return {'curso': curso_data}
        else:
            return {'error': 'No se encontró un estudiante asociado a este usuario o no tiene un curso asignado'}            