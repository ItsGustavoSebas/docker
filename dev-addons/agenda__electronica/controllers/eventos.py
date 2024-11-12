from odoo import http
from odoo.http import request, Response
from datetime import datetime
import json

class AgendaEventoController(http.Controller):

    @http.route('/api/eventos', type='http', auth='user', methods=['GET'])
    def get_user_eventos(self):
        # Obtener el usuario actual
        current_user_id = request.env.user.id

        # Intentar identificar si el usuario es un estudiante
        estudiante = request.env['agenda.estudiante'].search([('user_id', '=', current_user_id)], limit=1)

        # Intentar identificar si el usuario es un padre de familia
        padre_familia = request.env['agenda.padre_familia'].search([('user_id', '=', current_user_id)], limit=1)

        eventos_data = []

        if estudiante:
            # Si es un estudiante, buscar sus eventos
            eventos = request.env['agenda.evento_estudiante'].sudo().search(
                [('estudiante_id', '=', estudiante.id)],
                order='create_date desc'
            )
            for evento in eventos:
                eventos_data.append({
                    'id': evento.id,
                    'evento_id': evento.evento_id.id,
                    'tipo': evento.evento_id.tipo,
                    'descripcion': evento.evento_id.descripcion,
                    'archivo_documento': evento.evento_id.archivo_documento,
                    'resumen': evento.evento_id.resumen,
                    'fecha': evento.evento_id.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'leido': evento.leido,
                    'asistencia': evento.asistencia,
                    'confirmacion': evento.confirmacion,
                    'estudiante_id': evento.estudiante_id.id,
                })

        elif padre_familia:
            # Si es un padre de familia, buscar eventos para todos sus estudiantes relacionados
            eventos = request.env['agenda.evento_estudiante'].sudo().search(
                [('estudiante_id', 'in', padre_familia.estudiante_ids.ids)],
                order='create_date desc'
            )
            for evento in eventos:
                eventos_data.append({
                    'id': evento.id,
                    'evento_id': evento.evento_id.id,
                    'tipo': evento.evento_id.tipo,
                    'descripcion': evento.evento_id.descripcion,
                    'archivo_documento': evento.evento_id.archivo_documento,
                    'resumen': evento.evento_id.resumen,
                    'fecha': evento.evento_id.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'leido': evento.leido,
                    'asistencia': evento.asistencia,
                    'confirmacion': evento.confirmacion,
                    'estudiante_id': evento.estudiante_id.id,
                    'estudiante': evento.estudiante_id.name,
                })

        else:
            # Si el usuario no es estudiante ni padre de familia, retornar un error
            return Response(
                json.dumps({'status': 'error', 'message': 'No tienes permisos para acceder a los eventos'}),
                content_type='application/json',
                status=403
            )

        # Crear la respuesta como un JSON serializado
        response_content = json.dumps({
            'status': 'success',
            'eventos': eventos_data,
        })

        # Envolver la respuesta en un objeto Response con tipo de contenido JSON
        return Response(response_content, content_type='application/json', status=200)

        
    @http.route('/api/evento/confirmar/<int:evento_id>', type='http', auth='user', methods=['POST'], csrf=False)
    def marcar_evento_confirmado(self, evento_id):
        """Marca un evento específica como confirmado"""
        evento = request.env['agenda.evento_estudiante'].browse(evento_id)
        if evento.exists():
            if not evento.confirmacion:
                evento.confirmacion = True
            return Response(
                json.dumps({'status': 'success', 'message': 'Se ha confirmado la asistencia al evento'}),
                content_type='application/json',
                status=200
            )
        else:
            return Response(
                json.dumps({'status': 'error', 'message': 'Error al confirmar el evento'}),
                content_type='application/json',
                status=500
            )
        
    @http.route('/api/evento/ver/<int:evento_id>', type='http', auth='user', methods=['GET'])
    def marcar_evento_leido(self, evento_id):
        """Marca un evento específica como confirmado"""
        evento = request.env['agenda.evento_estudiante'].browse(evento_id)
        if evento.exists():
            if not evento.leido:
                evento.leido = True
            evento_data = {
                'id': evento.id,
                'evento_id': evento.evento_id.id,
                'tipo': evento.evento_id.tipo,
                'descripcion': evento.evento_id.descripcion,
                'archivo_documento': evento.evento_id.archivo_documento,
                'resumen': evento.evento_id.resumen,
                'fecha': evento.evento_id.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'leido': evento.leido,
                'asistencia': evento.asistencia,
                'confirmacion': evento.confirmacion,
                'estudiante_id': evento.estudiante_id.id,
            }
            response_content = json.dumps({
                'status': 'success',
                'evento': evento_data,
            })

            # Envolver la respuesta en un objeto Response con tipo de contenido JSON
            return Response(response_content, content_type='application/json', status=200)
        else:
            return Response(
                json.dumps({'status': 'error', 'message': 'Error al confirmar el evento'}),
                content_type='application/json',
                status=500
            )
        
    
