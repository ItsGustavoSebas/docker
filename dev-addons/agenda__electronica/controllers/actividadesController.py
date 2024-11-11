# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import dropbox
import base64
import json
import requests 

class ActividadController(http.Controller):


    @http.route('/api/get_actividades/<int:user_id>', type='json', auth='user', methods=['GET'])
    def get_actividades(self, user_id):
       # Verifica que el usuario especificado existe
        user = request.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            return {'error': 'Usuario no encontrado'}

        # Consulta las actividades asignadas al usuario en la tabla intermedia `usuario_actividad`
        actividades = request.env['agenda.actividad'].sudo().search([
            ('usuario_actividad_ids.usuario_id', '=', user.id)
        ])

        # Serializar los datos de los actividades para retornar en JSON
        data = []
        for actividad in actividades:
            # Modificar el archivo_url para reemplazar el nombre del archivo por "archivo"
            archivo_url = actividad.archivo_url
            if archivo_url:
                archivo_url = "/".join(archivo_url.split("/")[:-1]) + "/archivo"
                formato_archivo = actividad.archivo_url.split('.')[-1] if actividad.archivo_url and '.' in actividad.archivo_url else None
                
            download_url = actividad.public_url or ''
            if '?dl=0' in download_url:
                download_url = download_url.replace('?dl=0', '?dl=1')


            entregas_data = []
            for entrega in actividad.entregas_ids:
                archivo_nombre = entrega.archivo_nombre or ''
                formato_archivo = archivo_nombre.split('.')[-1] if '.' in archivo_nombre else ''

                entregas_data.append({
                    'id': entrega.id,
                    'estudiante_id': entrega.estudiante_id.id,
                    'estudiante_nombre': entrega.estudiante_id.name,
                    'archivo_nombre': entrega.archivo_nombre,
                    'puntaje': entrega.puntaje,
                    'fecha_entrega': entrega.fecha_entrega,
                    'url_publica': entrega.url_publica,
                    'formatoArchivo': formato_archivo,
                    # Puedes agregar más campos aquí si es necesario
                })
                
            data.append({
                'id': actividad.id,
                'motivo': actividad.motivo,
                'texto': actividad.texto,
                'archivo_url': archivo_url,
                'fecha_creacion': actividad.create_date,
                'fecha_presentacion': actividad.fecha_presentacion,
                'fecha_inicio': actividad.fecha_inicio,
                'curso_docente_materia_id': actividad.curso_docente_materia_id,
                'curso_materia': f"{actividad.curso_docente_materia_id.id_curso.display_name} - {actividad.curso_docente_materia_id.id_docente_materia.id_materia.name}",
                'entregas': entregas_data,  # Añade los datos de entregas
                'formatoarchivo': formato_archivo,
                'publicURL': download_url,
            })

        return {'actividades': data}


    @http.route('/api/marcar-actividad-leido/<int:user_id>/<int:actividad_id>', auth='user', methods=['POST'], csrf=False, type='json')
    def marcar_actividad_leido(self, user_id, actividad_id):
        try:
            # Verificar si el usuario existe
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return {'error': f'Usuario con ID {user_id} no encontrado'}

            # Verificar si el actividad existe
            actividad = request.env['agenda.actividad'].sudo().browse(actividad_id)
            if not actividad.exists():
                return {'error': f'actividad con ID {actividad_id} no encontrado'}

            # Buscar la relación en agenda.usuario_actividad
            usuario_actividad = request.env['agenda.usuario_actividad'].sudo().search([
                ('usuario_id', '=', user_id),
                ('actividad_id', '=', actividad_id)
            ], limit=1)

            if usuario_actividad:
                # Marcar como leído
                usuario_actividad.leido = True
                return {'status': 'success', 'message': 'actividad marcado como leído'}
            else:
                return {'error': 'No se encontró relación entre el usuario y el actividad'}
        except Exception as e:
            return {'error': str(e)}, 500            



    @http.route('/api/actividad/create', auth='user', methods=['POST'], csrf=False, type='http')
    def create_actividad(self, **kwargs):
        # Leer los datos enviados a través de form-data
        motivo = kwargs.get('motivo')
        texto = kwargs.get('texto')
        archivo_file = kwargs.get('archivo')
        archivo_nombre = archivo_file.filename if archivo_file else None
        curso_docente_materia_id = int(kwargs.get('curso_docente_materia_id', 0))
        fecha_inicio = kwargs.get('fecha_inicio')  # Formato esperado: 'YYYY-MM-DD HH:MM:SS'
        fecha_presentacion = kwargs.get('fecha_presentacion')  # Formato esperado: 'YYYY-MM-DD HH:MM:SS'


        # Validar campos requeridos
        if not motivo or not texto:
            return request.make_response(json.dumps({'error': 'El motivo y el texto son obligatorios'}), 
                                         headers={'Content-Type': 'application/json'})

        try:
            archivo_data = archivo_file.read() if archivo_file else None
            archivo_base64 = base64.b64encode(archivo_data).decode('utf-8') if archivo_data else None

            curso_docente_materia = request.env['agenda.curso_docente_materia'].sudo().browse(int(curso_docente_materia_id))
            if not curso_docente_materia.exists():
                return request.make_response(json.dumps({'error': 'El curso y materia seleccionado no existe o fue eliminado'}),
                                             headers={'Content-Type': 'application/json'})
            # Crear los valores iniciales para el actividad
            actividad_vals = {
                'motivo': motivo,
                'texto': texto,
                'archivo_nombre': archivo_nombre,
                'archivo': archivo_base64, 
                'curso_docente_materia_id': curso_docente_materia_id,
                'fecha_inicio': fecha_inicio,
                'fecha_presentacion': fecha_presentacion,
            }

            # Crear actividad en el modelo
            actividad = request.env['agenda.actividad'].sudo().create(actividad_vals)

            # Subir el archivo a Dropbox si existe
            if archivo_file and archivo_nombre:
                # Obtener el access token dinámicamente
                access_token = self.obtener_access_token()

                # Autenticación con el nuevo access_token
                dbx = dropbox.Dropbox(access_token)
                file_path = f'/{archivo_nombre}'
                archivo_decodificado = base64.b64decode(archivo_base64)
                dbx.files_upload(archivo_decodificado, file_path, mode=dropbox.files.WriteMode.overwrite, mute=True)

                # Obtener o crear enlace público en Dropbox
                shared_links = dbx.sharing_list_shared_links(path=file_path).links
                if shared_links:
                    download_url = shared_links[0].url.replace("?dl=0", "?dl=1")
                else:
                    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
                    download_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")
                
                actividad.public_url = download_url

            # Procesar roles y asignar usuarios en agenda.usuario_actividad
            usuarios_permitidos = self._obtener_usuarios_permitidos(actividad)
            
            # Crear registros en la tabla intermedia agenda.usuario_actividad
            for usuario in usuarios_permitidos:
                # Verificar si ya existe un registro para el usuario y la actividad
                usuario_actividad_existente = request.env['agenda.usuario_actividad'].sudo().search([
                    ('usuario_id', '=', usuario.id),
                    ('actividad_id', '=', actividad.id)
                ], limit=1)
                
                # Solo crear el registro si no existe
                if not usuario_actividad_existente:
                    request.env['agenda.usuario_actividad'].sudo().create({
                        'usuario_id': usuario.id,
                        'actividad_id': actividad.id,
                        'enviado': True,
                        'leido': False,
                    })
            # Devolver la respuesta en formato JSON
            return request.make_response(json.dumps({
                'status': 'success', 
                'actividad_id': actividad.id, 
                'public_url': actividad.public_url
            }), headers={'Content-Type': 'application/json'})

        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return request.make_response(json.dumps({'error': str(e)}), 
                                         headers={'Content-Type': 'application/json'})


    @http.route('/api/actividad/edit/<int:actividad_id>', auth='user', methods=['POST'], csrf=False, type='http')
    def edit_actividad(self, actividad_id, **kwargs):
        # Leer los datos enviados a través de form-data
        motivo = kwargs.get('motivo')
        texto = kwargs.get('texto')
        archivo_file = kwargs.get('archivo')
        archivo_nombre = archivo_file.filename if archivo_file else None
        curso_docente_materia_id = int(kwargs.get('curso_docente_materia_id', 0))
        fecha_inicio = kwargs.get('fecha_inicio')  # Formato esperado: 'YYYY-MM-DD HH:MM:SS'
        fecha_presentacion = kwargs.get('fecha_presentacion')  # Formato esperado: 'YYYY-MM-DD HH:MM:SS'
    
        # Validar campos requeridos
        if not motivo or not texto:
            return request.make_response(json.dumps({'error': 'El motivo y el texto son obligatorios'}), 
                                         headers={'Content-Type': 'application/json'})
    
        try:
            # Obtener el usuario actual y el administrativo correspondiente
            user = request.env.user
            # Buscar el actividad existente
            actividad = request.env['agenda.actividad'].sudo().search([('id', '=', actividad_id)], limit=1)
            if not actividad:
                return request.make_response(json.dumps({'error': 'actividad no encontrado'}), 
                                             headers={'Content-Type': 'application/json'})
    
            # Preparar los valores para actualizar el actividad
            actividad_vals = {
                'motivo': motivo,
                'texto': texto,
                'archivo_nombre': archivo_nombre,
                'curso_docente_materia_id': curso_docente_materia_id,
                'fecha_inicio': fecha_inicio,
                'fecha_presentacion': fecha_presentacion,
            }
    
            # Si se proporciona un archivo nuevo, actualizar el archivo y subirlo a Dropbox
            if archivo_file and archivo_nombre:
                archivo_extesion = archivo_nombre 
                archivo_url = f"/web/content/agenda.actividad/{actividad_id}/{archivo_extesion}"
                archivo_data = archivo_file.read()
                archivo_base64 = base64.b64encode(archivo_data).decode('utf-8')
                actividad_vals['archivo'] = archivo_base64
                actividad_vals['archivo_url'] = archivo_url
    
                # Obtener el access token dinámicamente
                access_token = self.obtener_access_token()
    
                # Autenticación con el nuevo access_token
                dbx = dropbox.Dropbox(access_token)
                file_path = f'/{archivo_nombre}'
                dbx.files_upload(archivo_data, file_path, mode=dropbox.files.WriteMode.overwrite, mute=True)
    
                # Obtener o crear enlace público en Dropbox
                shared_links = dbx.sharing_list_shared_links(path=file_path).links
                if shared_links:
                    download_url = shared_links[0].url.replace("?dl=0", "?dl=1")
                else:
                    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
                    download_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")
                
                actividad.public_url = download_url
            else:
                # Si no hay archivo nuevo, mantener el archivo actual
                actividad_vals['public_url'] = actividad.public_url
    
            # Actualizar el actividad con los valores proporcionados
            actividad.sudo().write(actividad_vals)
    
            usuarios_permitidos = self._obtener_usuarios_permitidos(actividad)
            
            # Crear registros en la tabla intermedia agenda.usuario_actividad
            for usuario in usuarios_permitidos:
                # Verificar si ya existe un registro para el usuario y la actividad
                usuario_actividad_existente = request.env['agenda.usuario_actividad'].sudo().search([
                    ('usuario_id', '=', usuario.id),
                    ('actividad_id', '=', actividad.id)
                ], limit=1)
                
                # Solo crear el registro si no existe
                if not usuario_actividad_existente:
                    request.env['agenda.usuario_actividad'].sudo().create({
                        'usuario_id': usuario.id,
                        'actividad_id': actividad.id,
                        'enviado': True,
                        'leido': False,
                    })
    
            # Devolver la respuesta en formato JSON
            return request.make_response(json.dumps({
                'status': 'success', 
                'actividad_id': actividad.id, 
                'public_url': actividad.public_url
            }), headers={'Content-Type': 'application/json'})
    
        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return request.make_response(json.dumps({'error': str(e)}), 
                                         headers={'Content-Type': 'application/json'})



    @http.route('/api/actividad/delete/<int:actividad_id>', auth='user', methods=['DELETE'], csrf=False, type='json')
    def delete_actividad(self, actividad_id):
        # Buscar el actividad
        actividad = request.env['agenda.actividad'].sudo().search([('id', '=', actividad_id)], limit=1)

        if not actividad:
            # Responder con error si no se encuentra el actividad
            return {'status': 'error', 'message': 'actividad no encontrado'}

        try:
            # Eliminar el actividad
            actividad.unlink()
            # Respuesta exitosa
            return {'status': 'success', 'message': 'actividad eliminado correctamente'}
        except Exception as e:
            # Manejar errores de eliminación
            return {'status': 'error', 'message': f'Error al eliminar el actividad: {str(e)}'}                                         



    def obtener_access_token(self):
        client_id = "geob75yb6u7h1zc"
        client_secret = "qxc0uucnyvs4q85"
        refresh_token = "bZTyFYYGNPEAAAAAAAAAAX1SF_PnxxcJ5rsoAl3RDmoNCxdijNFtxj_CnmeDvG71"
        
        url = "https://api.dropbox.com/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "OdooBot/1.0"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        data = "grant_type=refresh_token&refresh_token={}&client_id={}&client_secret={}".format(
        refresh_token, client_id, client_secret)

        try:
            response = requests.post(url, headers=headers, data=data)
            
            # Depuración para verificar el resultado
            print("Status Code:", response.status_code)
            print("Response JSON:", response.json())
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                raise Exception(f"Error al obtener access token: {response.json()}")
        
        except Exception as e:
            print("Error durante la solicitud:", e)
            raise Exception(f"Error al obtener access token: {str(e)}")


    def _obtener_usuarios_permitidos(self, actividad):
        """Lógica para obtener los usuarios permitidos basada en la actividad"""
        curso_docente_materia = actividad.curso_docente_materia_id
        curso = curso_docente_materia.id_curso

        # Estudiantes del curso
        estudiantes = curso.estudiante_ids

        # Padres de los estudiantes
        padres = estudiantes.mapped('padre_familia_ids')

        # Docente asignado a la actividad
        docente = curso_docente_materia.id_docente_materia.id_docente

        # Usuarios permitidos: estudiantes, padres y el docente
        usuarios = estudiantes.mapped('user_id') | padres.mapped('user_id') | docente.user_id
        
        return usuarios


    @http.route('/api/actividad/lectores/<int:actividad_id>', type='json', auth='user', methods=['GET'])
    def get_lectores_actividad(self, actividad_id):
        # Buscar el actividad correspondiente
        actividad = request.env['agenda.actividad'].sudo().browse(actividad_id)
        
        # Verificar si existe el actividad
        if not actividad.exists():
            return {'error': 'actividad no encontrado'}

        # Obtener todos los usuarios relacionados con el actividad y sus estados
        lectores_data = []
        for usuario_actividad in actividad.usuario_actividad_ids:
            lectores_data.append({
                'usuario_id': usuario_actividad.usuario_id.id,
                'nombre': usuario_actividad.usuario_id.name,
                'leido': usuario_actividad.leido,
                'enviado': usuario_actividad.enviado
            })

        # Retornar la lista de usuarios con el estado de lectura y envío en formato JSON
        return {'lectores': lectores_data} 




    @http.route('/api/get_actividades_curso/<int:curso_id>', type='json', auth='user', methods=['GET'])
    def get_actividades_por_curso(self, curso_id):
        # Verifica que el curso especificado existe
        curso = request.env['agenda.curso'].sudo().browse(curso_id)
        if not curso.exists():
            return {'error': 'Curso no encontrado'}

        # Consulta las actividades asignadas al curso en la tabla intermedia `curso_docente_materia_id`
        actividades = request.env['agenda.actividad'].sudo().search([
            ('curso_docente_materia_id.id_curso', '=', curso.id)
        ])

        # Serializar los datos de los actividades para retornar en JSON
        data = []
        for actividad in actividades:
            # Modificar el archivo_url para reemplazar el nombre del archivo por "archivo"
            archivo_url = actividad.archivo_url
            if archivo_url:
                archivo_url = "/".join(archivo_url.split("/")[:-1]) + "/archivo"
                formato_archivo = actividad.archivo_url.split('.')[-1] if actividad.archivo_url and '.' in actividad.archivo_url else None
                
            download_url = actividad.public_url or ''
            if '?dl=0' in download_url:
                download_url = download_url.replace('?dl=0', '?dl=1')


            entregas_data = []
            for entrega in actividad.entregas_ids:
                archivo_nombre = entrega.archivo_nombre or ''
                formato_archivo = archivo_nombre.split('.')[-1] if '.' in archivo_nombre else ''

                entregas_data.append({
                    'id': entrega.id,
                    'estudiante_id': entrega.estudiante_id.id,
                    'estudiante_nombre': entrega.estudiante_id.name,
                    'archivo_nombre': entrega.archivo_nombre,
                    'puntaje': entrega.puntaje,
                    'fecha_entrega': entrega.fecha_entrega,
                    'url_publica': entrega.url_publica,
                    'formatoArchivo': formato_archivo,
                    # Puedes agregar más campos aquí si es necesario
                })
                
            data.append({
                'id': actividad.id,
                'motivo': actividad.motivo,
                'texto': actividad.texto,
                'archivo_url': archivo_url,
                'fecha_creacion': actividad.create_date,
                'fecha_presentacion': actividad.fecha_presentacion,
                'fecha_inicio': actividad.fecha_inicio,
                'curso_docente_materia_id': actividad.curso_docente_materia_id,
                'curso_materia': f"{actividad.curso_docente_materia_id.id_curso.display_name} - {actividad.curso_docente_materia_id.id_docente_materia.id_materia.name}",
                'entregas': entregas_data,  # Añade los datos de entregas
                'formatoarchivo': formato_archivo,
                'publicURL': download_url,
            })

        return {'actividades': data}



    @http.route('/api/get_actividad_estadisticas/<int:curso_id>', type='json', auth='user', methods=['GET'])
    def get_actividad_estadisticas(self, curso_id):
        # Verifica que el curso especificado existe
        curso = request.env['agenda.curso'].sudo().browse(curso_id)
        if not curso.exists():
            return {'error': 'Curso no encontrado'}

        # Consulta las actividades asignadas al curso en la tabla intermedia `curso_docente_materia_id`
        actividades = request.env['agenda.actividad'].sudo().search([
            ('curso_docente_materia_id.id_curso', '=', curso.id)
        ])

        # Diccionario para almacenar información de cada estudiante
        estudiantes_data = {}
        
        # Serializar los datos de las actividades y calcular las estadísticas
        for actividad in actividades:
            fecha_creacion = actividad.fecha_inicio
            for entrega in actividad.entregas_ids:
                estudiante = entrega.estudiante_id
                nombre_estudiante = estudiante.name

                # Calcular días entre fecha de creación de actividad y entrega
                dias_entrega = (entrega.fecha_entrega - fecha_creacion).days if entrega.fecha_entrega else 0
                puntaje = entrega.puntaje

                if estudiante.id not in estudiantes_data:
                    estudiantes_data[estudiante.id] = {
                        'nombre': nombre_estudiante,
                        'total_dias_entrega': 0,
                        'total_puntaje': 0.0,
                        'entregas_count': 0
                    }

                # Sumar datos del estudiante
                estudiantes_data[estudiante.id]['total_dias_entrega'] += dias_entrega
                estudiantes_data[estudiante.id]['total_puntaje'] += puntaje
                estudiantes_data[estudiante.id]['entregas_count'] += 1

        # Calcular promedios
        resultados = []
        for estudiante_id, datos in estudiantes_data.items():
            entregas_count = datos['entregas_count']
            promedio_dias_entrega = round(datos['total_dias_entrega'] / entregas_count, 0) if entregas_count > 0 else 0
            promedio_puntaje = round(datos['total_puntaje'] / entregas_count, 0) if entregas_count > 0 else 0

            resultados.append({
                'estudiante_id': estudiante_id,
                'nombre': datos['nombre'],
                'promedio_dias_entrega': promedio_dias_entrega,
                'promedio_puntaje': promedio_puntaje
            })

        return {'estadisticas': resultados}