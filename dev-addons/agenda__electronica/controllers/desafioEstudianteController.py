from odoo import http
from odoo.http import request

class DesafioEstudianteController(http.Controller):

    @http.route('/api/desafios_estudiante/<int:user_id>', type='json', auth='public', methods=['GET'])
    def get_desafios_estudiante_por_user_id(self, user_id):
        # Buscar al estudiante correspondiente al user_id
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        if not estudiante:
            return {'error': 'Estudiante no encontrado'}

        # Buscar los registros en desafio_estudiante para este estudiante
        desafios_estudiante = request.env['agenda.desafio_estudiante'].sudo().search([
            ('estudiante_id', '=', estudiante.id),
            ('puntaje', '=', 0) 
        ])

        if not desafios_estudiante:
            return {'error': 'No se encontraron desafíos para este estudiante'}

        # Obtener los ID de desafíos en los que participa el estudiante
        desafio_ids = desafios_estudiante.mapped('desafio_id.id')

        # Buscar otros registros en desafio_estudiante que tengan los mismos desafio_ids
        desafios_compartidos = request.env['agenda.desafio_estudiante'].sudo().search([
            ('desafio_id', 'in', desafio_ids),
            ('estudiante_id', '!=', estudiante.id)  # Excluir al estudiante original
        ])

        # Preparar la respuesta con los detalles de cada desafío compartido
        desafios_estudiante_data = []
        for desafio_est in desafios_compartidos:
            desafios_estudiante_data.append({
                'desafio_id': desafio_est.desafio_id.id,
                'estudiante_companero_id': desafio_est.estudiante_id.id,
                'companero_user_id': desafio_est.estudiante_id.user_id.id,
                'estudiante_companero_nombre': desafio_est.estudiante_id.name,
                'puntaje_companero': desafio_est.puntaje,
                'puntaje_estudiante': 0
            })

        return {'status': 'success', 'desafios_estudiante': desafios_estudiante_data}




    @http.route('/api/desafios_completados_estudiante/<int:user_id>', type='json', auth='public', methods=['GET'])
    def get_desafios_completados_estudiante_por_user_id(self, user_id):
        # Buscar al estudiante correspondiente al user_id
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        if not estudiante:
            return {'error': 'Estudiante no encontrado'}

        # Buscar los registros en desafio_estudiante para este estudiante
        desafios_estudiante = request.env['agenda.desafio_estudiante'].sudo().search([
            ('estudiante_id', '=', estudiante.id),
            ('puntaje', '!=', 0) 
        ])

        if not desafios_estudiante:
            return {'error': 'No se encontraron desafíos para este estudiante'}

        # Obtener los ID de desafíos en los que participa el estudiante
        desafio_ids = desafios_estudiante.mapped('desafio_id.id')

        # Buscar otros registros en desafio_estudiante que tengan los mismos desafio_ids
        desafios_compartidos = request.env['agenda.desafio_estudiante'].sudo().search([
            ('desafio_id', 'in', desafio_ids),
            ('estudiante_id', '!=', estudiante.id)  # Excluir al estudiante original
        ])

        # Preparar la respuesta con los detalles de cada desafío compartido
        desafios_estudiante_data = []
        for desafio_est in desafios_compartidos:

            puntaje_estudiante = request.env['agenda.desafio_estudiante'].sudo().search([
                ('desafio_id', '=', desafio_est.desafio_id.id),
                ('estudiante_id', '=', estudiante.id)
            ], limit=1).puntaje           

            desafios_estudiante_data.append({
                'desafio_id': desafio_est.desafio_id.id,
                'estudiante_companero_id': desafio_est.estudiante_id.id,
                'companero_user_id': desafio_est.estudiante_id.user_id.id,
                'estudiante_companero_nombre': desafio_est.estudiante_id.name,
                'puntaje_companero': desafio_est.puntaje,
                'puntaje_estudiante': puntaje_estudiante

            })

        return {'status': 'success', 'desafios_estudiante': desafios_estudiante_data}        




    @http.route('/api/desafios_estudiante/resultados/<int:estudiante_id>', type='json', auth='public', methods=['GET'])
    def get_resultados_desafios_estudiante(self, estudiante_id):
        # Buscar al estudiante en base a su ID
        estudiante = request.env['agenda.estudiante'].sudo().search([('id', '=', estudiante_id)], limit=1)
        
        if not estudiante:
            return {'error': 'Estudiante no encontrado'}

        # Obtener la configuración (asumiendo que solo existe una)
        configuracion = request.env['agenda.configuraciones'].sudo().search([], limit=1)
        if not configuracion:
            return {'error': 'Configuración no encontrada'}

        puntos_valor = configuracion.puntos

        # Obtener los desafíos completados por el estudiante
        desafios_estudiante = request.env['agenda.desafio_estudiante'].sudo().search([
            ('estudiante_id', '=', estudiante.id),
            ('puntaje', '!=', 0)
        ])

        desafios_ganados = 0
        desafios_perdidos = 0

        for desafio_est in desafios_estudiante:
            # Buscar el desafío del compañero en el mismo desafio_id y con puntaje distinto de 0
            desafio_companero = request.env['agenda.desafio_estudiante'].sudo().search([
                ('desafio_id', '=', desafio_est.desafio_id.id),
                ('estudiante_id', '!=', estudiante.id),
                ('puntaje', '!=', 0)
            ], limit=1)

            if desafio_companero:
                # Comparar puntajes solo si ambos tienen puntajes distintos de 0
                if desafio_est.puntaje > desafio_companero.puntaje:
                    desafios_ganados += 1
                elif desafio_est.puntaje < desafio_companero.puntaje:
                    desafios_perdidos += 1

        # Calcular puntos ganados y perdidos
        puntos_ganados = desafios_ganados * puntos_valor
        puntos_perdidos = desafios_perdidos * puntos_valor

        # Devolver la respuesta en formato JSON
        return {
            'status': 'success',
            'resultados': {
                'puntos_ganados': puntos_ganados,
                'puntos_perdidos': puntos_perdidos
            }
        }