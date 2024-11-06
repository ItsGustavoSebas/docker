from odoo import models, fields, api
import html
import base64
import requests  # Importa el módulo requests
import dropbox
import firebase_admin
from firebase_admin import credentials, messaging


class Comunicado(models.Model):
    _name = 'agenda.comunicado'
    _description = 'Comunicado'

    motivo = fields.Char(string='Motivo', required=True)
    texto = fields.Text(string='Texto', required=True)
    archivo = fields.Binary(string='Archivo Adjunto')
    archivo_url = fields.Char(string="Archivo URL", compute="_compute_archivo_url", store=True)
    archivo_imagen_html = fields.Html(string="Imagen HTML", compute="_compute_archivo_imagen_html", sanitize=False, store=False)
    archivo_video_html = fields.Html(string="Video HTML", compute="_compute_archivo_video_html", sanitize=False, store=False)
    archivo_audio_html = fields.Html(string="Audio HTML", compute="_compute_archivo_audio_html", sanitize=False, store=False)
    public_url = fields.Char(string="Public URL", store=True)


    archivo_nombre = fields.Char(string="Nombre del Archivo", store=True)  # Campo para almacenar el nombre con extensión.
    # Relación con los Administrativos (Many2one)
    administrativo_id = fields.Many2one(
        'agenda.administrativo', 
        string='Emitido por', 
        ondelete='set null',
        readonly=True
    )

    # Relación Many2many con Roles
    rol_ids = fields.Many2many(
        'roles.role', 
        string='Enviar a Roles'
    )

    # Relación con Usuarios que han leído el comunicado (Tabla Intermedia)
    usuario_comunicado_ids = fields.One2many(
        'agenda.usuario_comunicado', 
        'comunicado_id', 
        string='Usuarios que han leído'
    )


    def ver_leidos(self):
        """Abre el modal con la lista de usuarios que han leído el comunicado."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Usuarios Leídos',
            'res_model': 'agenda.usuario_comunicado',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('comunicado_id', '=', self.id)],
            'context': {'create': False}, 
        }
    

    def action_guardar_y_volver(self):
        """Guardar el comunicado y volver a la lista."""
        domain = ['|', ('rol_ids', '=', False), ('rol_ids.user_ids', 'in', [self.env.uid])]

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Comunicados',
            'res_model': 'agenda.comunicado',
            'view_mode': 'list',
            'target': 'current',
            'domain': domain,
        }        


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



    @api.model
    def create(self, vals):
        """Asignar automáticamente al administrativo actual como emisor y crear registros en usuario_comunicado."""
        user = self.env.user
        archivo_data = vals.get('archivo')
        administrativo = self.env['agenda.administrativo'].search([('user_id', '=', user.id)], limit=1)
        if not administrativo:
            raise models.ValidationError("Solo un administrativo puede emitir un comunicado.")

        # Asignar el administrativo actual como emisor
        vals['administrativo_id'] = administrativo.id

        archivo_nombre = vals.get('archivo_nombre')

        # Crear el comunicado
        comunicado = super(Comunicado, self).create(vals)

        if comunicado.archivo and comunicado.archivo_nombre:
            archivo_extesion = comunicado.archivo_nombre 
            comunicado.archivo_url = f"/web/content/{comunicado._name}/{comunicado.id}/{archivo_extesion}"

        if archivo_data and archivo_nombre:
            try:
                # Obtén el access_token usando el refresh_token
                access_token = self.obtener_access_token()
                
                # Conéctate a Dropbox con el nuevo access_token
                dbx = dropbox.Dropbox(access_token)

                # Decodificar el archivo y subirlo a Dropbox
                archivo_decodificado = base64.b64decode(archivo_data)
                file_path = f'/{archivo_nombre}'
                dbx.files_upload(archivo_decodificado, file_path, mode=dropbox.files.WriteMode.overwrite,  mute=True)

                # Intenta obtener o crear el enlace público
                shared_links = dbx.sharing_list_shared_links(path=file_path).links
                if shared_links:
                    download_url = shared_links[0].url.replace("?dl=0", "?dl=1")
                else:
                    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
                    download_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")

                comunicado.public_url = download_url

            except Exception as e:
                raise Exception(f"Error al obtener o crear el enlace compartido en Dropbox: {e}")
        else:
            comunicado.archivo_url = ""


        # Si no se seleccionaron roles, obtener todos los usuarios
        if not comunicado.rol_ids:
            usuarios = self.env['res.users'].search([])
        else:
            # Obtener los usuarios de los roles seleccionados
            usuarios = self.env['res.users'].search([
                ('id', 'in', self.env['roles.role'].browse(comunicado.rol_ids.ids).mapped('user_ids.id'))
            ])



        # Crear registros en la tabla intermedia agenda.usuario_comunicado
        for usuario in usuarios:
            self.env['agenda.usuario_comunicado'].create({
                'usuario_id': usuario.id,
                'comunicado_id': comunicado.id,
                'enviado': True,
                'leido': False,
            })

        return comunicado


    def ver_comunicado(self):
        """Marcar como leído y abrir la vista detallada del comunicado."""
        usuario = self.env.user
    
        # Buscar el registro correspondiente en la tabla usuario_comunicado
        usuario_comunicado = self.env['agenda.usuario_comunicado'].search([
            ('comunicado_id', '=', self.id),
            ('usuario_id', '=', usuario.id)
        ], limit=1)
    
        # Si el registro existe, marcarlo como leído
        if usuario_comunicado:
            usuario_comunicado.leido = True
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ver Comunicado',
            'res_model': 'agenda.comunicado',
            'view_mode': 'form',
            'view_id': self.env.ref('agenda__electronica.view_html_comunicado').id,
            'target': 'new',
            'res_id': self.id,
        }


    @api.depends('archivo_url')
    def _compute_archivo_imagen_html(self):
        for record in self:
            if record.archivo_url and record.archivo_url.endswith(('.jpg', '.png')):
                archivo_url_modificado = "/".join(record.archivo_url.split("/")[:-1]) + "/archivo"
                # Generamos el código HTML para la imagen
                record.archivo_imagen_html = f'<img src="{html.escape(archivo_url_modificado)}" alt="Imagen no disponible" style="max-width: 100%; height: auto;"/>'
            else:
                record.archivo_imagen_html = ''


    @api.depends('archivo_url')
    def _compute_archivo_video_html(self):
        for record in self:
            if record.archivo_url and record.archivo_url.endswith('.mp4'):
                archivo_url_modificado = "/".join(record.archivo_url.split("/")[:-1]) + "/archivo"
                # Generamos el código HTML para el video
                record.archivo_video_html = (
                    f'<video controls style="max-width: 100%; height: auto;">'
                    f'<source src="{html.escape(archivo_url_modificado)}" type="video/mp4">'
                    'Tu navegador no soporta la reproducción de video.'
                    '</video>'
                )
            else:
                record.archivo_video_html = ''          

    @api.depends('archivo_url')
    def _compute_archivo_audio_html(self):
        for record in self:
            if record.archivo_url and record.archivo_url.endswith('.mp3'):
                # Reemplazar el nombre del archivo por 'archivo' en la URL
                archivo_url_modificado = "/".join(record.archivo_url.split("/")[:-1]) + "/archivo"
                
                # Generar el HTML para el audio
                record.archivo_audio_html = (
                    f'<audio controls style="width: 100%;">'
                    f'<source src="{html.escape(archivo_url_modificado)}" type="audio/mp3">'
                    'Tu navegador no soporta la reproducción de audio.'
                    '</audio>'
                )
            else:
                record.archivo_audio_html = ''   
    

    @api.onchange('archivo')
    def _onchange_archivo(self):
        """Captura el nombre del archivo subido."""
        if self.archivo:
            # Si el archivo tiene un nombre asociado, guardarlo
            archivo_nombre = self.env.context.get('bin_size', '')  # Capturar nombre del contexto.
            if archivo_nombre:
                self.archivo_nombre = archivo_nombre
            else:
                self.archivo_nombre = 'archivo_desconocido'    
