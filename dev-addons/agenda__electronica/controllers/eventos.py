from odoo import http
from odoo.http import request, Response
from datetime import datetime
import json

class AgendaEventoController(http.Controller):

    @http.route('/api/eventos', type='http', auth='user', methods=['GET'])
    def get_user_eventos(self):
        # Obtener el usuario actual
        current_user_id = request.env.user.id
        # Filtrar los eventos para el usuario logueado
        estudiante = request.env['agenda.estudiante'].search([('user_id', '=', current_user_id)], limit=1)
        eventos = request.env['agenda.evento_estudiante'].sudo().search(
            [('estudiante_id', '=', estudiante.id)],
            order='create_date desc'
        )
        
        # Convertir las notificaciones a un formato serializable en JSON
        eventos_data = []
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
                'confirmacion': evento.confirmacion,
                'estudiante_id': evento.estudiante_id.id,
            })
        
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
        if evento.exists() and evento.estudiante_id.user_id.id == request.env.user.id:
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
        if evento.exists() and evento.estudiante_id.user_id.id == request.env.user.id:
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
        
    
