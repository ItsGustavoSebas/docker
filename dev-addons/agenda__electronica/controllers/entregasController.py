# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import dropbox
import base64
import json
import requests 

class EntregasController(http.Controller):

    @http.route('/api/entregas/<int:actividad_id>', type='json', auth='user', methods=['GET'])
    def get_entregas(self, actividad_id):
        # Buscar el actividad correspondiente
        actividad = request.env['agenda.actividad'].sudo().browse(actividad_id)
        
        # Verificar si existe el actividad
        if not actividad.exists():
            return {'error': 'Actividad no encontrada'}

        # Obtener todas las entregas asociadas al actividad
        entregas_data = []
        for entrega in actividad.entregas_ids:
            entregas_data.append({
                'id': entrega.id,
                'estudiante_id': entrega.estudiante_id.id,
                'estudiante_nombre': entrega.estudiante_id.name,
                'archivo_nombre': entrega.archivo_nombre,
                'puntaje': entrega.puntaje,
                'fecha_entrega': entrega.fecha_entrega,
                'url_publica': entrega.url_publica,
                # Agrega otros campos relevantes aquí si es necesario
            })

        # Retornar las entregas en formato JSON
        return {'entregas': entregas_data}



    @http.route('/api/entregas/create', type='http', auth='user', methods=['POST'], csrf=False)
    def create_entrega(self, **kwargs):
        # Obtener valores enviados desde el formulario
        actividad_id = int(kwargs.get('actividad_id', 0))
        user_id = int(kwargs.get('user_id', 0))  # Se recibe el user_id
        archivo_file = kwargs.get('archivo')

        # Verificar que la actividad exista
        actividad = request.env['agenda.actividad'].sudo().browse(actividad_id)
        if not actividad.exists():
            return request.make_response(json.dumps({'error': 'Actividad no encontrada'}), 
                                         headers={'Content-Type': 'application/json'})

        # Buscar el estudiante usando el user_id proporcionado
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        if not estudiante:
            return request.make_response(json.dumps({'error': 'Estudiante no encontrado para el user_id proporcionado'}), 
                                         headers={'Content-Type': 'application/json'})

        if not actividad.exists() or not estudiante.exists():
            return request.make_response(json.dumps({'error': 'Actividad o Estudiante no encontrado'}), 
                                         headers={'Content-Type': 'application/json'})

        # Crear el archivo en base64 para almacenar en Odoo y asignar nombre
        archivo_nombre = archivo_file.filename if archivo_file else None
        archivo_base64 = base64.b64encode(archivo_file.read()).decode('utf-8') if archivo_file else None

        # Definir los valores para crear la entrega, con puntaje predeterminado 0
        entrega_vals = {
            'actividad_id': actividad.id,
            'estudiante_id': estudiante.id,
            'puntaje': 0.0,
            'archivo_nombre': archivo_nombre,
            'archivo': archivo_base64,
            'fecha_entrega': fields.Datetime.now(),
        }

        # Crear la entrega en Odoo
        entrega = request.env['agenda.actividad_entrega'].sudo().create(entrega_vals)

        # Subir el archivo a Dropbox si existe y guardar el URL público
        if archivo_file:
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
                
                actividad.url_publica = download_url

        # Devolver respuesta con los datos de la entrega
        entrega_data = {
            'id': entrega.id,
            'estudiante_id': entrega.estudiante_id.id,
            'estudiante_nombre': entrega.estudiante_id.name,
            'archivo_nombre': entrega.archivo_nombre,
            'puntaje': entrega.puntaje,
            'fecha_entrega': entrega.fecha_entrega.strftime('%Y-%m-%d %H:%M:%S'),  # Convertir a cadena
            'url_publica': entrega.url_publica,
        }

        return request.make_response(json.dumps({'entrega': entrega_data}), headers={'Content-Type': 'application/json'})

    @http.route('/api/entregas/edit/<int:entrega_id>', auth='user', methods=['POST'], csrf=False, type='http')
    def edit_entrega(self, entrega_id, **kwargs):
        entrega = request.env['agenda.actividad_entrega'].sudo().browse(entrega_id)
        
        # Verificar si la entrega existe
        if not entrega.exists():
            return request.make_response(json.dumps({'error': 'Entrega no encontrada'}), headers={'Content-Type': 'application/json'})

        # Leer los datos enviados a través de form-data
        archivo_file = kwargs.get('archivo')
        archivo_nombre = archivo_file.filename if archivo_file else entrega.archivo_nombre  # Mantener nombre actual si no hay archivo
        puntaje = kwargs.get('puntaje') or entrega.puntaje  # Mantener puntaje actual si no se envía
  

        entrega_vals = {
            'archivo_nombre': archivo_nombre,
            'puntaje': puntaje,
        }

        # Subir archivo a Dropbox y obtener la URL pública si hay un archivo nuevo
        if archivo_file and archivo_nombre:
            archivo_data = archivo_file.read()
            archivo_base64 = base64.b64encode(archivo_data).decode('utf-8')
            entrega_vals['archivo'] = archivo_base64
            
            # Acceso a Dropbox
            access_token = self.obtener_access_token()
            dbx = dropbox.Dropbox(access_token)
            file_path = f'/{archivo_nombre}'
            dbx.files_upload(archivo_data, file_path, mode=dropbox.files.WriteMode.overwrite, mute=True)
            
            # Obtener o crear enlace público
            shared_links = dbx.sharing_list_shared_links(path=file_path).links
            if shared_links:
                download_url = shared_links[0].url.replace("?dl=0", "?dl=1")
            else:
                shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
                download_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")

            entrega_vals['url_publica'] = download_url
        else:
            # Si no hay archivo nuevo, mantener la URL pública actual
            entrega_vals['url_publica'] = entrega.url_publica

        # Actualizar la entrega con los valores proporcionados
        entrega.sudo().write(entrega_vals)

        # Preparar datos de respuesta
        entrega_data = {
            'id': entrega.id,
            'estudiante_id': entrega.estudiante_id.id,
            'estudiante_nombre': entrega.estudiante_id.name,
            'archivo_nombre': entrega.archivo_nombre,
            'puntaje': entrega.puntaje,
            'url_publica': entrega.url_publica,
        }

        # Responder con los datos de la entrega actualizados
        return request.make_response(json.dumps({'entrega': entrega_data}), headers={'Content-Type': 'application/json'})


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




    @http.route('/api/entregas/existe/<int:actividad_id>/<int:user_id>', type='json', auth='user', methods=['GET'])
    def verificar_entrega(self, actividad_id, user_id):
        # Buscar el estudiante usando el user_id proporcionado
        estudiante = request.env['agenda.estudiante'].sudo().search([('user_id', '=', user_id)], limit=1)
        
        if not estudiante:
            return {'error': 'Estudiante no encontrado para el user_id proporcionado'}

        # Buscar la entrega para el estudiante y el comunicado específico (actividad_id)
        entrega_existente = request.env['agenda.actividad_entrega'].sudo().search([
            ('actividad_id', '=', actividad_id),
            ('estudiante_id', '=', estudiante.id)
        ], limit=1)

        # Devolver respuesta JSON indicando si existe o no la entrega
        if entrega_existente:
            return {'existe': True, 'entrega_id': entrega_existente.id}
        else:
            return {'existe': False}