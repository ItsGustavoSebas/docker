from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response
import json

class DeviceTokenController(http.Controller):

    @http.route('/api/device_token/<string:token>', type='json', auth='user', methods=['POST'], csrf=False)
    def update_device_token(self, token):
        """
        Actualiza el token de dispositivo del usuario autenticado. 
        Si el usuario ya tiene 2 tokens, elimina el más antiguo.
        """
        user = request.env.user

        existing_token = request.env['user.device.token'].sudo().search([('user_id', '=', user.id), ('device_token', '=', token)], limit=1)
        if existing_token:
            return Response(
                json.dumps({'status': 'success', 'message': 'El token ya existe para este usuario.'}),
                content_type='application/json',
                status=200
            )

        user_tokens = request.env['user.device.token'].sudo().search([('user_id', '=', user.id)], order='create_date ASC')
        if len(user_tokens) >= 2:
            user_tokens[0].unlink()

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
