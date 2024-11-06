# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import dropbox
import base64
import json
import requests 

class ComunicadoController(http.Controller):


    @http.route('/api/get_comunicados/<int:user_id>', type='json', auth='user', methods=['GET'])
    def get_comunicados(self, user_id):
        # Obtén el usuario especificado
        user = request.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            return {'error': 'Usuario no encontrado'}

        # Consulta los comunicados dirigidos al rol del usuario o sin roles asignados
        comunicados = request.env['agenda.comunicado'].sudo().search([
            '|',
            ('rol_ids.user_ids', 'in', user.id),
            ('rol_ids', '=', False)
        ])

        # Serializar los datos de los comunicados para retornar en JSON
        data = []
        for comunicado in comunicados:
            # Modificar el archivo_url para reemplazar el nombre del archivo por "archivo"
            archivo_url = comunicado.archivo_url
            if archivo_url:
                archivo_url = "/".join(archivo_url.split("/")[:-1]) + "/archivo"
                formato_archivo = comunicado.archivo_url.split('.')[-1] if comunicado.archivo_url and '.' in comunicado.archivo_url else None
                
            download_url = comunicado.public_url or ''
            if '?dl=0' in download_url:
                download_url = download_url.replace('?dl=0', '?dl=1')
            data.append({
                'id': comunicado.id,
                'motivo': comunicado.motivo,
                'texto': comunicado.texto,
                'archivo_url': archivo_url,
                'administrativo': comunicado.administrativo_id.name if comunicado.administrativo_id else None,
                'fecha_creacion': comunicado.create_date,
                'roles': [role.name for role in comunicado.rol_ids],
                'formatoarchivo': formato_archivo,
                'publicURL': download_url,
            })

        return {'comunicados': data}


    @http.route('/api/marcar_comunicado_leido', type='json', auth='user', methods=['POST'])
    def marcar_comunicado_leido(self, user_id, comunicado_id):
        # Verificar si el usuario y el comunicado existen
        user = request.env['res.users'].sudo().browse(user_id)
        comunicado = request.env['agenda.comunicado'].sudo().browse(comunicado_id)
        
        if not user.exists():
            return {'error': 'Usuario no encontrado'}
        if not comunicado.exists():
            return {'error': 'Comunicado no encontrado'}
        
        # Buscar el registro en agenda.usuario_comunicado que vincule al usuario y al comunicado
        usuario_comunicado = request.env['agenda.usuario_comunicado'].sudo().search([
            ('usuario_id', '=', user_id),
            ('comunicado_id', '=', comunicado_id)
        ], limit=1)

        if usuario_comunicado:
            # Marcar el comunicado como leído
            usuario_comunicado.leido = True
            return {'status': 'success', 'message': 'Comunicado marcado como leído'}
        else:
            return {'error': 'No se encontró relación entre el usuario y el comunicado'}        



    @http.route('/api/comunicado/create', auth='user', methods=['POST'], csrf=False, type='http')
    def create_comunicado(self, **kwargs):
        # Leer los datos enviados a través de form-data
        motivo = kwargs.get('motivo')
        texto = kwargs.get('texto')
        archivo_file = kwargs.get('archivo')
        archivo_nombre = archivo_file.filename if archivo_file else None
        rol_ids = json.loads(kwargs.get('rol_ids', '[]'))  # Convertir a lista de IDs

        # Validar campos requeridos
        if not motivo or not texto:
            return request.make_response(json.dumps({'error': 'El motivo y el texto son obligatorios'}), 
                                         headers={'Content-Type': 'application/json'})

        try:
            # Obtener el usuario actual y el administrativo correspondiente
            user = request.env.user
            administrativo = request.env['agenda.administrativo'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not administrativo:
                return request.make_response(json.dumps({'error': 'Solo un administrativo puede emitir un comunicado'}), 
                                             headers={'Content-Type': 'application/json'})


            archivo_data = archivo_file.read() if archivo_file else None
            archivo_base64 = base64.b64encode(archivo_data).decode('utf-8') if archivo_data else None
            # Crear los valores iniciales para el comunicado
            comunicado_vals = {
                'motivo': motivo,
                'texto': texto,
                'administrativo_id': administrativo.id,
                'archivo_nombre': archivo_nombre,
                'archivo': archivo_base64, 
                'rol_ids': [(6, 0, rol_ids)]
            }

            # Crear comunicado en el modelo
            comunicado = request.env['agenda.comunicado'].sudo().create(comunicado_vals)

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
                
                comunicado.public_url = download_url

            # Procesar roles y asignar usuarios en agenda.usuario_comunicado
            if not comunicado.rol_ids:
                usuarios = request.env['res.users'].sudo().search([])
            else:
                usuarios = request.env['res.users'].sudo().search([('id', 'in', comunicado.rol_ids.mapped('user_ids').ids)])
            
            # Devolver la respuesta en formato JSON
            return request.make_response(json.dumps({
                'status': 'success', 
                'comunicado_id': comunicado.id, 
                'public_url': comunicado.public_url
            }), headers={'Content-Type': 'application/json'})

        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return request.make_response(json.dumps({'error': str(e)}), 
                                         headers={'Content-Type': 'application/json'})


    @http.route('/api/comunicado/edit/<int:comunicado_id>', auth='user', methods=['POST'], csrf=False, type='http')
    def edit_comunicado(self, comunicado_id, **kwargs):
        # Leer los datos enviados a través de form-data
        motivo = kwargs.get('motivo')
        texto = kwargs.get('texto')
        archivo_file = kwargs.get('archivo')
        archivo_nombre = archivo_file.filename if archivo_file else None
        rol_ids = json.loads(kwargs.get('rol_ids', '[]'))  # Convertir a lista de IDs
    
        # Validar campos requeridos
        if not motivo or not texto:
            return request.make_response(json.dumps({'error': 'El motivo y el texto son obligatorios'}), 
                                         headers={'Content-Type': 'application/json'})
    
        try:
            # Obtener el usuario actual y el administrativo correspondiente
            user = request.env.user
            administrativo = request.env['agenda.administrativo'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not administrativo:
                return request.make_response(json.dumps({'error': 'Solo un administrativo puede editar un comunicado'}), 
                                             headers={'Content-Type': 'application/json'})
    
            # Buscar el comunicado existente
            comunicado = request.env['agenda.comunicado'].sudo().search([('id', '=', comunicado_id)], limit=1)
            if not comunicado:
                return request.make_response(json.dumps({'error': 'Comunicado no encontrado'}), 
                                             headers={'Content-Type': 'application/json'})
    
            # Preparar los valores para actualizar el comunicado
            comunicado_vals = {
                'motivo': motivo,
                'texto': texto,
                'archivo_nombre': archivo_nombre,
                'rol_ids': [(6, 0, rol_ids)]
            }
    
            # Si se proporciona un archivo nuevo, actualizar el archivo y subirlo a Dropbox
            if archivo_file and archivo_nombre:
                archivo_extesion = archivo_nombre 
                archivo_url = f"/web/content/agenda.comunicado/{comunicado_id}/{archivo_extesion}"
                archivo_data = archivo_file.read()
                archivo_base64 = base64.b64encode(archivo_data).decode('utf-8')
                comunicado_vals['archivo'] = archivo_base64
                comunicado_vals['archivo_url'] = archivo_url
    
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
                
                comunicado.public_url = download_url
            else:
                # Si no hay archivo nuevo, mantener el archivo actual
                comunicado_vals['public_url'] = comunicado.public_url
    
            # Actualizar el comunicado con los valores proporcionados
            comunicado.sudo().write(comunicado_vals)
    
            # Procesar roles y asignar usuarios en agenda.usuario_comunicado
            if not comunicado.rol_ids:
                usuarios = request.env['res.users'].sudo().search([])
            else:
                usuarios = request.env['res.users'].sudo().search([('id', 'in', comunicado.rol_ids.mapped('user_ids').ids)])
            
            # Actualizar la asignación de usuarios para el comunicado
            request.env['agenda.usuario_comunicado'].sudo().search([('comunicado_id', '=', comunicado.id)]).unlink()  # Eliminar asignaciones previas
            for usuario in usuarios:
                request.env['agenda.usuario_comunicado'].sudo().create({
                    'usuario_id': usuario.id,
                    'comunicado_id': comunicado.id,
                    'enviado': True,
                    'leido': False,
                })
    
            # Devolver la respuesta en formato JSON
            return request.make_response(json.dumps({
                'status': 'success', 
                'comunicado_id': comunicado.id, 
                'public_url': comunicado.public_url
            }), headers={'Content-Type': 'application/json'})
    
        except Exception as e:
            # En caso de error, devolver el mensaje en JSON
            return request.make_response(json.dumps({'error': str(e)}), 
                                         headers={'Content-Type': 'application/json'})



    @http.route('/api/comunicado/delete/<int:comunicado_id>', auth='user', methods=['DELETE'], csrf=False, type='json')
    def delete_comunicado(self, comunicado_id):
        # Buscar el comunicado
        comunicado = request.env['agenda.comunicado'].sudo().search([('id', '=', comunicado_id)], limit=1)

        if not comunicado:
            # Responder con error si no se encuentra el comunicado
            return {'status': 'error', 'message': 'Comunicado no encontrado'}

        try:
            # Eliminar el comunicado
            comunicado.unlink()
            # Respuesta exitosa
            return {'status': 'success', 'message': 'Comunicado eliminado correctamente'}
        except Exception as e:
            # Manejar errores de eliminación
            return {'status': 'error', 'message': f'Error al eliminar el comunicado: {str(e)}'}                                         



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
