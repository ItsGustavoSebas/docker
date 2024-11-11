from odoo import http
from odoo.http import request
import json
import random
import openai
import time

class DesafioController(http.Controller):

    def _configurar_api_openai(self):
        # Configura la clave de API de OpenAI
        openai.api_key = "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"

    
    def _generar_preguntas_con_ia(self, tema_categoria):
        self._configurar_api_openai()
        
        _logger = http.logging.getLogger(__name__)
        _logger.info("Iniciando generación de preguntas con IA para la categoría: %s", tema_categoria)
        
        # Construcción del prompt para la generación
        prompt = (
            f"Genera una lista de 3 preguntas de opción múltiple sobre {tema_categoria} esas preguntas deben ser podidas respondidas por jovenes de 10-15 de edad. "
            "Para cada pregunta, proporciona 3 opciones en formato JSON y especifica cuál es correcta. "
            "Devuelve las opciones en un orden aleatorio, asegurando que la opción correcta no esté siempre en la misma posición. "
            "Usa el siguiente formato: "
            "[{\"texto\": \"texto de la pregunta\", \"opciones\": [{\"texto\": \"opcion1\", \"is_correct\": false}, "
            "{\"texto\": \"opcion2\", \"is_correct\": true}, {\"texto\": \"opcion3\", \"is_correct\": false}]}]"
        )



        _logger.info("Prompt para OpenAI: %s", prompt)

        try:
            time.sleep(1) 
            # Llama a la API de OpenAI para obtener preguntas y opciones
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            _logger.info("Respuesta completa de OpenAI: %s", response)

            # Accede a 'choices' y al 'content' de la respuesta de manera correcta
            if hasattr(response, 'choices') and response.choices:
                texto_generado = response.choices[0].message.content

                # Limpieza del texto si incluye etiquetas de código
                if texto_generado.startswith("```json"):
                    texto_generado = texto_generado.strip("```json").strip("```")
                
                _logger.info("Texto generado por OpenAI (limpio): %s", texto_generado)
                
                preguntas = self._parsear_preguntas(texto_generado)
                _logger.info("Preguntas parseadas: %s", preguntas)
                
                return preguntas
            else:
                _logger.warning("No se recibieron opciones en 'choices' en la respuesta de OpenAI")
                return []


                
        except Exception as e:
            _logger.error("Error al llamar a OpenAI: %s", e)
            request.env['ir.logging'].sudo().create({
                'name': "Error de OpenAI",
                'type': "server",
                'dbname': request.env.cr.dbname,
                'level': "ERROR",
                'message': f"Error al generar preguntas: {e}",
                'path': "desafioController",
                'func': "_generar_preguntas_con_ia",
                'line': "Llamada a OpenAI"
            })
            return []

    def _parsear_preguntas(self, texto):
        try:
            preguntas_data = json.loads(texto)
            return preguntas_data
        except json.JSONDecodeError:
            _logger = http.logging.getLogger(__name__)
            _logger.error("Error al parsear JSON en _parsear_preguntas")
            return []
 

    # Crear una solicitud de desafío
    @http.route('/api/desafio/crear_solicitud', auth='user', methods=['POST'], csrf=False, type='json')
    def crear_solicitud_desafio(self):
        # Usar request.httprequest.get_json() para obtener el cuerpo JSON
        data = request.httprequest.get_json()
        desafiante_user_id = data.get('desafiante_id') if data else None
        desafiado_estudiante_id = data.get('desafiado_id') if data else None
        mensaje = data.get('mensaje', '¡Te desafio!')  # Valor por defecto

        # Log para verificar los valores capturados
        _logger = http.logging.getLogger(__name__)
        _logger.info("Valores recibidos - desafiante_user_id: %s, desafiado_user_id: %s, mensaje: %s", desafiante_user_id, desafiado_estudiante_id, mensaje)


        # Validación de campos requeridos
        if not desafiante_user_id or not desafiado_estudiante_id:
            return {'error': 'Los campos desafiante_id y desafiado_id son obligatorios'}

        # Buscar el estudiante que corresponde a desafiado_estudiante_id y obtener su user_id
        desafiado = request.env['agenda.estudiante'].sudo().browse(desafiado_estudiante_id)
        if not desafiado.exists():
            return {'error': f"El estudiante con id {desafiado_estudiante_id} no existe."}

        desafiado_user_id = desafiado.user_id.id
    


        if desafiante_user_id == desafiado_user_id:
            _logger.info("te desafiaste a ti mismo xd")
            return {'error': 'No puedes desafiarte a ti mismo'}

        # Buscar los estudiantes basándose en el user_id
        desafiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', desafiante_user_id)], limit=1)
        desafiado = request.env['agenda.estudiante'].sudo().search([('user_id', '=', desafiado_user_id)], limit=1)
        

        # Verificar que ambos estudiantes existen
        if not desafiante:
            return {'error': f"El desafiante con user_id {desafiante_user_id} no existe en la tabla de estudiantes."}
        if not desafiado:
            return {'error': f"El desafiado con user_id {desafiado_user_id} no existe en la tabla de estudiantes."}

        try:
            # Crear la solicitud de desafío
            solicitud = request.env['agenda.solicitud_desafio'].sudo().create({
                'desafiante_id': desafiante.id,
                'desafiado_id': desafiado.id,
                'is_aceptado': False,
                'mensaje': mensaje
            })

            # Respuesta JSON de éxito
            return {'status': 'success', 'solicitud_id': solicitud.id}
        
        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return {'error': str(e)}


    @http.route('/api/desafio/aceptar/<int:solicitud_id>', auth='user', methods=['POST'], type='json', csrf=False)
    def aceptar_desafio(self, solicitud_id):
        solicitud = request.env['agenda.solicitud_desafio'].sudo().browse(solicitud_id)
        if solicitud and not solicitud.is_aceptado:
            # Actualizar el estado de aceptación
            solicitud.sudo().write({'is_aceptado': True})
            # Llamar al método para crear el desafío completo
            return self._crear_desafio_completo(solicitud.desafiante_id.user_id.id, solicitud.desafiado_id.user_id.id)

        return {'status': 'error', 'message': 'La solicitud ya ha sido aceptada o no existe'}


    @http.route('/api/solicitud/delete/<int:solicitud_id>', auth='user', methods=['DELETE'], csrf=False, type='json')
    def delete_solicitud(self, solicitud_id):
        # Buscar la solicitud de desafío
        solicitud = request.env['agenda.solicitud_desafio'].sudo().search([('id', '=', solicitud_id)], limit=1)

        if not solicitud:
            # Responder con error si no se encuentra la solicitud
            return {'status': 'error', 'message': 'Solicitud de desafío no encontrada'}

        try:
            # Eliminar la solicitud de desafío
            solicitud.unlink()
            # Respuesta exitosa
            return {'status': 'success', 'message': 'Solicitud de desafío eliminada correctamente'}
        except Exception as e:
            # Manejar errores de eliminación
            return {'status': 'error', 'message': f'Error al eliminar la solicitud de desafío: {str(e)}'}




    @http.route('/api/desafio/solicitudes_recibidas/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def obtener_solicitudes_recibidas(self, user_id):
        # Buscar el estudiante correspondiente al user_id
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar que el estudiante existe
        if not estudiante:
            return {'status': 'error', 'message': f"No se encontró un estudiante con user_id {user_id}"}

        # Buscar solicitudes donde el estudiante sea el "desafiado"
        solicitudes = request.env['agenda.solicitud_desafio'].sudo().search([
            ('desafiado_id', '=', estudiante.id),
            ('is_aceptado', '=', False)  # Filtrar solo las solicitudes no aceptadas
        ])

        # Convertir los datos de las solicitudes a un formato JSON
        solicitudes_data = [{
            'id': solicitud.id,
            'desafiante_id': solicitud.desafiante_id.id,
            'desafiante_nombre': solicitud.desafiante_id.name,
            'fecha_solicitud': solicitud.fecha_solicitud,
            'mensaje': solicitud.mensaje
        } for solicitud in solicitudes]

        return {
            'status': 'success',
            'solicitudes': solicitudes_data
        }



    @http.route('/api/desafio/solicitudes_enviadas/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def obtener_solicitudes_enviadas(self, user_id):
        # Buscar el estudiante correspondiente al user_id
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar que el estudiante existe
        if not estudiante:
            return {'status': 'error', 'message': f"No se encontró un estudiante con user_id {user_id}"}
    
        # Buscar solicitudes donde el estudiante sea el "desafiante"
        solicitudes = request.env['agenda.solicitud_desafio'].sudo().search([
            ('desafiante_id', '=', estudiante.id),
            ('is_aceptado', '=', False)  # Filtrar solo las solicitudes no aceptadas
        ])
    
        # Convertir los datos de las solicitudes a un formato JSON
        solicitudes_data = [{
            'id': solicitud.id,
            'desafiado_id': solicitud.desafiado_id.id,
            'desafiado_nombre': solicitud.desafiado_id.name,
            'fecha_solicitud': solicitud.fecha_solicitud,
            'mensaje': solicitud.mensaje
        } for solicitud in solicitudes]
    
        return {
            'status': 'success',
            'solicitudes': solicitudes_data
        }


        
    def _crear_desafio_completo(self, user_id_1, user_id_2):
        # Buscar los estudiantes basándose en los user_id proporcionados
        estudiante_1 = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id_1)], limit=1)
        estudiante_2 = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id_2)], limit=1)

        if not estudiante_1 or not estudiante_2:
            return {'error': 'Uno o ambos estudiantes no fueron encontrados'}
    
        categorias = request.env['agenda.categoria'].sudo().search([])
        categoria = random.choice(categorias) if categorias else None
        if not categoria:
            return {'error': 'No se encontraron categorías'}

        # Generar preguntas utilizando OpenAI basado en la categoría seleccionada
        preguntas_data = self._generar_preguntas_con_ia(categoria.nombre)

        # Validar si preguntas_data es una lista de diccionarios
        if not isinstance(preguntas_data, list) or not all(isinstance(p, dict) for p in preguntas_data):
            return {'error': 'Formato de preguntas incorrecto'}


        # Crear el desafío
        desafio_vals = {'tema': categoria.nombre}
        desafio = request.env['agenda.desafio'].sudo().create(desafio_vals)

        # Crear relaciones entre estudiantes y desafío
        for estudiante in [estudiante_1, estudiante_2]:
            request.env['agenda.desafio_estudiante'].sudo().create({
                'desafio_id': desafio.id,
                'estudiante_id': estudiante.id,
                'puntaje': 0
            })

        # Procesar cada pregunta y sus opciones
        for pregunta_data in preguntas_data:
            texto_pregunta = pregunta_data.get('texto')
            opciones_data = pregunta_data.get('opciones')
    
            # Validar estructura de cada pregunta
            if not texto_pregunta or not isinstance(opciones_data, list):
                continue  # Si falta información en una pregunta, omitirla
    
            # Crear la pregunta
            pregunta_vals = {
                'texto': texto_pregunta,
                'desafio_id': desafio.id,
                'categoria_id': categoria.id
            }
            pregunta = request.env['agenda.pregunta'].sudo().create(pregunta_vals)
    
            # Crear las opciones para la pregunta
            for opcion_data in opciones_data:
                opcion_texto = opcion_data.get('texto')
                is_correct = opcion_data.get('is_correct', False)
                # Validar que la opción tenga el formato correcto
                if opcion_texto is not None and isinstance(is_correct, bool):
                    request.env['agenda.opciones'].sudo().create({
                        'opcion': opcion_texto,
                        'is_correct': is_correct,
                        'pregunta_id': pregunta.id
                    })
    

        return {
            'status': 'success',
            'desafio_id': desafio.id,
            'estudiantes': [estudiante_1.id, estudiante_2.id],
            'preguntas_creadas': len(preguntas_data),
            'opciones_por_pregunta': 3
        }




    @http.route('/api/desafio/<int:desafio_id>/preguntas/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def obtener_preguntas_por_desafio(self, desafio_id, user_id):
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar que el estudiante existe
        if not estudiante:
            return {'status': 'error', 'message': f"No se encontró un estudiante con user_id {user_id}"}
        
        estudiante_id = estudiante.id  # Obtener el estudiante_id

        # Buscar el desafío correspondiente al desafio_id
        desafio = request.env['agenda.desafio'].sudo().browse(desafio_id)
        
        # Verificar que el desafío existe
        if not desafio.exists():
            return {'status': 'error', 'message': f"No se encontró un desafío con id {desafio_id}"}
        
        # Buscar las preguntas asociadas al desafío
        preguntas = request.env['agenda.pregunta'].sudo().search([('desafio_id', '=', desafio_id)])
        
        # Filtrar preguntas en base a la selección del usuario en 'estudiante_opciones'
        preguntas_filtradas = []
        for pregunta in preguntas:
            # Verificar si alguna opción de la pregunta ya está seleccionada por el usuario
            opciones_seleccionadas = request.env['agenda.estudiante_opciones'].sudo().search([
                ('estudiante_id', '=', estudiante_id),
                ('opcion_id', 'in', pregunta.opciones_ids.ids)
            ])

            # Solo incluir la pregunta si no tiene opciones seleccionadas por el usuario
            if not opciones_seleccionadas:
                opciones_data = [{
                    'id': opcion.id,
                    'texto': opcion.opcion,
                    'is_correct': opcion.is_correct
                } for opcion in pregunta.opciones_ids]

                preguntas_filtradas.append({
                    'id': pregunta.id,
                    'texto': pregunta.texto,
                    'categoria_id': pregunta.categoria_id.id,
                    'categoria_nombre': pregunta.categoria_id.nombre,
                    'opciones': opciones_data
                })

        return {
            'status': 'success',
            'preguntas': preguntas_filtradas
        }


    @http.route('/api/desafio/<int:desafio_id>/calcular_puntaje/<int:user_id>', auth='user', methods=['GET'], type='json', csrf=False)
    def calcular_puntaje_desafio(self, desafio_id, user_id):
        # Convertir user_id a estudiante_id
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        # Verificar que el estudiante existe
        if not estudiante:
            return {'status': 'error', 'message': f"No se encontró un estudiante con user_id {user_id}"}
        
        estudiante_id = estudiante.id

        # Buscar todas las preguntas asociadas al desafío
        preguntas = request.env['agenda.pregunta'].sudo().search([('desafio_id', '=', desafio_id)])
        
        if not preguntas:
            return {'status': 'error', 'message': f"No se encontraron preguntas para el desafío con id {desafio_id}"}

        # Obtener todas las opciones seleccionadas por el estudiante para este desafío
        opciones_seleccionadas = request.env['agenda.estudiante_opciones'].sudo().search([
            ('estudiante_id', '=', estudiante_id),
            ('opcion_id', 'in', preguntas.mapped('opciones_ids').ids)  # Filtrar solo opciones relacionadas con las preguntas del desafío
        ])

        # Contadores para calcular el puntaje
        total_preguntas = len(preguntas)
        respuestas_correctas = 0

        # Verificar si las opciones seleccionadas son correctas
        for opcion_seleccionada in opciones_seleccionadas:
            if opcion_seleccionada.opcion_id.is_correct:
                respuestas_correctas += 1

        # Calcular el puntaje sobre 100
        puntaje = round((respuestas_correctas / total_preguntas) * 100) if total_preguntas > 0 else 0
        puntaje = max(puntaje, 1)  # Asegurarse de que el puntaje sea al menos 1

        _logger = http.logging.getLogger(__name__)
        _logger.info(f"Intentando actualizar puntaje en DesafioEstudiante con desafio_id: {desafio_id} y estudiante_id: {estudiante_id}")


        # Buscar el registro en DesafioEstudiante y actualizar el puntaje
        desafio_estudiante = request.env['agenda.desafio_estudiante'].sudo().search([
            ('desafio_id', '=', desafio_id),
            ('estudiante_id', '=', estudiante_id)
        ], limit=1)

        if desafio_estudiante:
            desafio_estudiante.sudo().write({'puntaje': puntaje})
        else:
            return {'status': 'error', 'message': 'No se encontró el registro en DesafioEstudiante para actualizar el puntaje'}

        return {
            'status': 'success',
            'puntaje': puntaje,
            'total_preguntas': total_preguntas,
            'respuestas_correctas': respuestas_correctas
        }




