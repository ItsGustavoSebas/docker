from odoo import http
from odoo.http import request
import json

class CursoMateriaDocenteController(http.Controller):

    @http.route('/api/curso_materia_docente/<int:user_id>', type='json', auth='user', methods=['GET'])
    def get_curso_materia_docente(self, user_id):
        # Obtiene el docente asociado al user_id
        docente = request.env['agenda.docente'].sudo().search([('user_id', '=', user_id)], limit=1)

        # Verificar si se encontró el docente
        if not docente:
            return {'error': 'Docente no encontrado'}

        # Consultar los registros de curso-materia para el docente encontrado
        cursos_materias = request.env['agenda.curso_docente_materia'].sudo().search([
            ('id_docente_materia.id_docente', '=', docente.id)
        ])

        # Serializar los datos de los cursos-materias
        data = []
        for curso_materia in cursos_materias:
            data.append({
                'id': curso_materia.id,
                'curso': curso_materia.id_curso.display_name,
                'materia': curso_materia.id_docente_materia.id_materia.name,
                'name': curso_materia.name,
                'nombre': f"{curso_materia.id_curso.display_name} - {curso_materia.id_docente_materia.id_materia.name}",
            })

        # Retornar los datos en formato JSON
        return {'cursos_materias': data}
