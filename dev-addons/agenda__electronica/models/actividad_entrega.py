from odoo import models, fields, api
import html
import base64
import requests  # Importa el módulo requests
import dropbox
import firebase_admin
from firebase_admin import credentials, messaging
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import AccessError

class ActividadEntrega(models.Model):
    _name = 'agenda.actividad_entrega'
    _description = 'Entrega de Actividad'

    actividad_id = fields.Many2one('agenda.actividad', string='Actividad', required=True, ondelete='restrict')
    estudiante_id = fields.Many2one('agenda.estudiante', string='Estudiante', required=True, ondelete='restrict')
    archivo = fields.Binary(string='Archivo Entregado', required=True)
    puntaje = fields.Float(string='Puntaje', default=0.0)
    fecha_entrega = fields.Datetime(string='Fecha de Entrega', default=fields.Datetime.now)
    archivo_nombre = fields.Char(string="Nombre del Archivo", store=True)
    url_publica = fields.Char(string="URL Pública", readonly=True, store=True) 

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



    def subir_a_dropbox(self):
        """Sube el archivo a Dropbox y guarda el enlace público en `url_publica`."""
        if not self.archivo or not self.archivo_nombre:
            raise ValidationError("No se ha adjuntado un archivo para subir.")
        
        try:
            # Obtén el access_token usando el método obtener_access_token
            access_token = self.obtener_access_token()
            dbx = dropbox.Dropbox(access_token)
            
            # Decodificar el archivo y subirlo a Dropbox
            archivo_decodificado = base64.b64decode(self.archivo)
            file_path = f'/{self.archivo_nombre}'
            dbx.files_upload(archivo_decodificado, file_path, mode=dropbox.files.WriteMode.overwrite, mute=True)
            
            # Obtener el enlace público
            shared_links = dbx.sharing_list_shared_links(path=file_path).links
            if shared_links:
                download_url = shared_links[0].url.replace("?dl=0", "?dl=1")
            else:
                shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
                download_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")
            
            # Guardar el enlace público en el campo url_publica
            self.url_publica = download_url

        except Exception as e:
            raise ValidationError(f"Error al subir el archivo a Dropbox: {e}")


    def action_calificar(self):
        """Acción para calificar la entrega."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calificar Entrega',
            'res_model': 'agenda.actividad_entrega',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def _onchange_archivo(self):
         """Captura el nombre del archivo subido y lo guarda en archivo_nombre."""
         if self.archivo:
             archivo_nombre = self.env.context.get('filename')  # Obtener el nombre del archivo desde el contexto
             if archivo_nombre:
                 self.archivo_nombre = archivo_nombre
             else:
                 self.archivo_nombre = 'archivo_desconocido'

    @api.model
    def create(self, vals):
        """Sobrescribe create para subir el archivo a Dropbox al crear una nueva entrega."""
        record = super(ActividadEntrega, self).create(vals)
        if 'archivo' in vals:
            record.subir_a_dropbox()
        return record

    def write(self, vals):
        """Sobrescribe write para volver a subir el archivo a Dropbox si se modifica."""
        res = super(ActividadEntrega, self).write(vals)
        if 'archivo' in vals:
            self.subir_a_dropbox()
        return res                 