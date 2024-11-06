from odoo import http
from odoo.http import request

class RolController(http.Controller):

    @http.route('/api/roles', auth='user', methods=['GET'], type='json', csrf=False)
    def get_roles(self):
        roles = request.env['roles.role'].sudo().search([])
        roles_data = [{'id': role.id, 'name': role.name} for role in roles]
        
        return {'roles': roles_data}
        

    @http.route('/api/rol-permisos/<int:user_id>', auth='public', methods=['GET'], csrf=False, type='json')
    def obtener_rol_permisos(self, user_id):
        try:
            user = request.env['res.users'].sudo().browse(user_id)

            if not user.exists():
                return {'error': f'Usuario con ID {user_id} no encontrado'}

            roles = user.role_ids  # Obtener roles del usuario
            data = []

            for role in roles:
                permisos = role.permiso_ids.mapped('name')
                data.append({
                    'role_name': role.name,
                    'permissions': permisos
                })

            return {'roles': data}
        except Exception as e:
            return {'error': str(e)}, 500


    @http.route('/api/marcar-comunicado-leido/<int:user_id>/<int:comunicado_id>', auth='user', methods=['POST'], csrf=False, type='json')
    def marcar_comunicado_leido(self, user_id, comunicado_id):
        try:
            # Verificar si el usuario existe
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return {'error': f'Usuario con ID {user_id} no encontrado'}

            # Verificar si el comunicado existe
            comunicado = request.env['agenda.comunicado'].sudo().browse(comunicado_id)
            if not comunicado.exists():
                return {'error': f'Comunicado con ID {comunicado_id} no encontrado'}

            # Buscar la relación en agenda.usuario_comunicado
            usuario_comunicado = request.env['agenda.usuario_comunicado'].sudo().search([
                ('usuario_id', '=', user_id),
                ('comunicado_id', '=', comunicado_id)
            ], limit=1)

            if usuario_comunicado:
                # Marcar como leído
                usuario_comunicado.leido = True
                return {'status': 'success', 'message': 'Comunicado marcado como leído'}
            else:
                return {'error': 'No se encontró relación entre el usuario y el comunicado'}
        except Exception as e:
            return {'error': str(e)}, 500            