from odoo import http
from odoo.http import request
import json

class ConfiguracionesController(http.Controller):

    @http.route('/api/configuracion/get', type='json', auth='public', methods=['GET'])
    def get_configuracion(self):
        # Buscar el registro de configuración único
        configuracion = request.env['agenda.configuraciones'].sudo().search([], limit=1)
        
        if not configuracion:
            return {'error': 'Configuración no encontrada'}

        # Devolver los valores de la configuración en formato JSON
        configuracion_data = {
            'puntos': configuracion.puntos,
            'frecuencia': configuracion.frecuencia,
        }
        return {'status': 'success', 'configuracion': configuracion_data}


    @http.route('/api/configuracion/edit', auth='user', methods=['POST'], csrf=False, type='http')
    def edit_configuracion(self, **kwargs):
        # Leer los datos enviados a través de form-data
        puntos = int(kwargs.get('puntos', 0))
        frecuencia = int(kwargs.get('frecuencia', 0))
        
        if puntos <= 0 or frecuencia <= 0:
            return request.make_response(json.dumps({'error': 'Los valores de puntos y frecuencia deben ser mayores a 0'}), 
                                         headers={'Content-Type': 'application/json'})

        try:
            # Buscar la configuración existente
            configuracion = request.env['agenda.configuraciones'].sudo().search([], limit=1)
            if not configuracion:
                return request.make_response(json.dumps({'error': 'Configuración no encontrada'}), 
                                             headers={'Content-Type': 'application/json'})

            # Actualizar la configuración con los valores proporcionados
            configuracion_vals = {
                'puntos': puntos,
                'frecuencia': frecuencia,
            }
            configuracion.sudo().write(configuracion_vals)

            # Devolver la respuesta en formato JSON
            return request.make_response(json.dumps({
                'status': 'success', 
                'configuracion': {
                    'puntos': configuracion.puntos,
                    'frecuencia': configuracion.frecuencia,
                }
            }), headers={'Content-Type': 'application/json'})

        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return request.make_response(json.dumps({'error': str(e)}), 
                                         headers={'Content-Type': 'application/json'})
