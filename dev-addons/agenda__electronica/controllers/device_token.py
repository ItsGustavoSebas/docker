from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response
import json

class DeviceTokenController(http.Controller):

    @http.route('/api/device_token/<string:token>', type='json', auth='user', methods=['POST'], csrf=False)
    def update_device_token(self, token):
        """
        Actualiza el token de dispositivo del usuario autenticado.
        """
        user = request.env.user

        # Crear un nuevo registro en 'user.device.token'
        request.env['user.device.token'].sudo().create({
            'user_id': user.id,
            'device_token': token
        })

        return Response(
            json.dumps({'status': 'success', 'message': 'Token actualizado'}),
            content_type='application/json',
            status=200
        )
