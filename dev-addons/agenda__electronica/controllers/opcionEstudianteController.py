from odoo import http
from odoo.http import request

class OpcionEstudianteController(http.Controller):

    # Ruta para seleccionar una opción en una pregunta de desafío
    @http.route('/api/seleccionar_opcion/<int:user_id>/<int:opcion_id>', auth='user', methods=['POST'], type='json', csrf=False)
    def seleccionar_opcion(self, user_id, opcion_id):
        # Verificar que el estudiante (usuario) existe
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        if not estudiante:
            return {'status': 'error', 'message': f"No se encontró un estudiante con user_id {user_id}"}
        
        # Verificar que la opción existe
        opcion = request.env['agenda.opciones'].sudo().browse(opcion_id)
        if not opcion.exists():
            return {'status': 'error', 'message': f"No se encontró una opción con id {opcion_id}"}

        # Verificar si ya existe una selección de esta opción para el estudiante
        seleccion_existente = request.env['agenda.estudiante_opciones'].sudo().search([
            ('estudiante_id', '=', estudiante.id),
            ('opcion_id', '=', opcion_id)
        ], limit=1)

        if seleccion_existente:
            return {'status': 'error', 'message': "Esta opción ya fue seleccionada por el estudiante."}

        # Crear la relación de la opción seleccionada por el estudiante
        seleccion = request.env['agenda.estudiante_opciones'].sudo().create({
            'estudiante_id': estudiante.id,
            'opcion_id': opcion_id
        })

        return {
            'status': 'success',
            'message': "Opción seleccionada correctamente",
            'seleccion_id': seleccion.id
        }
