from odoo import http
from odoo.http import request, Response
from datetime import datetime
import json

class AgendaNotificacionController(http.Controller):

    @http.route('/api/notificaciones', type='http', auth='user', methods=['GET'])
    def get_user_notifications(self):
        # Obtener el usuario actual
        current_user_id = request.env.user.id
        # Filtrar las notificaciones para el usuario logueado
        notifications = request.env['agenda.notificacion'].sudo().search(
            [('user_id', '=', current_user_id)],
            order='create_date desc'
        )
        
        # Convertir las notificaciones a un formato serializable en JSON
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'data': notification.data,
                'read_at': notification.read_at.isoformat() if notification.read_at else False,
                'user_id': notification.user_id.id,
            })
        
        # Crear la respuesta como un JSON serializado
        response_content = json.dumps({
            'status': 'success',
            'notifications': notifications_data,
        })

        # Envolver la respuesta en un objeto Response con tipo de contenido JSON
        return Response(response_content, content_type='application/json', status=200)
        
    @http.route('/api/notificacion/marcar/<int:notification_id>', type='http', auth='user', methods=['POST'], csrf=False)
    def mark_notification_as_read(self, notification_id):
        """Marca una notificación específica como leída"""
        notification = request.env['agenda.notificacion'].browse(notification_id)
        if notification.exists() and notification.user_id.id == request.env.user.id:
            if not notification.read_at:
                notification.read_at = datetime.now()
            return Response(
                json.dumps({'status': 'success', 'message': 'Todas las notificaciones fueron marcadas como leídas'}),
                content_type='application/json',
                status=200
            )
        else:
            return Response(
                json.dumps({'status': 'error', 'message': 'Error al marcar la notificacion como leida'}),
                content_type='application/json',
                status=500
            )
        
    @http.route('/api/notificaciones/marcartodas', type='http', auth='user', methods=['POST'], csrf=False)
    def mark_all_notifications_as_read(self):
        """Marca todas las notificaciones del usuario actual como leídas"""
        current_user_id = request.env.user.id
        # Filtrar las notificaciones no leídas del usuario actual
        notifications = request.env['agenda.notificacion'].sudo().search([('user_id', '=', current_user_id), ('read_at', '=', False)])
        
        # Marcar todas las notificaciones como leídas
        notifications.write({'read_at': datetime.now()})
        
        return Response(
            json.dumps({'status': 'success', 'message': 'Todas las notificaciones fueron marcadas como leídas'}),
            content_type='application/json',
            status=200
        )
