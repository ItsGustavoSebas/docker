from odoo import http
from odoo.http import request
import json

class CategoriaController(http.Controller):

    @http.route('/api/categorias', auth='user', methods=['GET'], type='json', csrf=False)
    def get_categorias(self):
        categorias = request.env['agenda.categoria'].sudo().search([])
        categorias_data = [{
            'id': categoria.id,
            'nombre': categoria.nombre,
            # Si tienes otros campos en `Categoria`, inclúyelos aquí
        } for categoria in categorias]
        
        return {'categorias': categorias_data}


    @http.route('/api/categoria/create', auth='user', methods=['POST'], csrf=False, type='json')
    def create_categoria(self):
        # Usar request.httprequest.get_json() para obtener el cuerpo JSON
        data = request.httprequest.get_json()
        nombre = data.get('nombre') if data else None
        
        # Log para verificar el valor capturado
        _logger = http.logging.getLogger(__name__)
        _logger.info("Valor de 'nombre' recibido: %s", nombre)
        
        # Validación de campo requerido
        if not nombre:
            return {'error': 'El nombre de la categoría es obligatorio'}
        
        try:
            # Crear la categoría
            categoria_vals = {
                'nombre': nombre,
            }
            categoria = request.env['agenda.categoria'].sudo().create(categoria_vals)
            
            # Respuesta JSON de éxito
            return {'status': 'success', 'categoria_id': categoria.id}
        
        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return {'error': str(e)}





    @http.route('/api/categoria/delete/<int:categoria_id>', auth='user', methods=['DELETE'], csrf=False, type='json')
    def delete_categoria(self, categoria_id):
        # Buscar el categoria
        categoria = request.env['agenda.categoria'].sudo().search([('id', '=', categoria_id)], limit=1)

        if not categoria:
            # Responder con error si no se encuentra el categoria
            return {'status': 'error', 'message': 'categoria no encontrado'}

        try:
            # Eliminar el categoria
            categoria.unlink()
            # Respuesta exitosa
            return {'status': 'success', 'message': 'categoria eliminado correctamente'}
        except Exception as e:
            # Manejar errores de eliminación
            return {'status': 'error', 'message': f'Error al eliminar el categoria: {str(e)}'}                                         

