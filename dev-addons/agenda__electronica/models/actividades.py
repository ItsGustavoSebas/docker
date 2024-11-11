from odoo import models, fields, api
import html
import base64
import requests  # Importa el módulo requests
import dropbox
import firebase_admin
from firebase_admin import credentials, messaging
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import AccessError


class Actividad(models.Model):
    _name = 'agenda.actividad'
    _description = 'actividad'

    motivo = fields.Char(string='Motivo', required=True)
    texto = fields.Text(string='Texto', required=True)
    archivo = fields.Binary(string='Archivo Adjunto', required=True)
    fecha_inicio = fields.Datetime(string='Fecha de Inicio', required=True)
    fecha_presentacion = fields.Datetime(string='Fecha de Presentación')
    archivo_url = fields.Char(string="Archivo URL", compute="_compute_archivo_url", store=True)
    archivo_imagen_html = fields.Html(string="Imagen HTML", compute="_compute_archivo_imagen_html", sanitize=False, store=False)
    archivo_video_html = fields.Html(string="Video HTML", compute="_compute_archivo_video_html", sanitize=False, store=False)
    archivo_audio_html = fields.Html(string="Audio HTML", compute="_compute_archivo_audio_html", sanitize=False, store=False)
    public_url = fields.Char(string="Public URL", store=True)

    allowed_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios Permitidos',
        compute='_compute_allowed_users',
        store=True
    )


    entregas_ids = fields.One2many(
        'agenda.actividad_entrega', 
        'actividad_id', 
        string='Entregas',
        ondelete='set null',
    )

    matching_user = fields.Boolean(string="Usuario coincide", compute="_compute_matching_user")


    archivo_nombre = fields.Char(string="Nombre del Archivo", store=True)  # Campo para almacenar el nombre con extensión.

    # En el modelo
    curso_docente_materia_id = fields.Many2one(
        'agenda.curso_docente_materia',
        string='Curso y Materia',
        required=True,
        domain="[('id_docente_materia.id_docente.user_id', '=', uid)]",
        context={'show_name': True}
    )
    

    # Relación con Usuarios que han leído el actividad (Tabla Intermedia)
    usuario_actividad_ids = fields.One2many(
        'agenda.usuario_actividad', 
        'actividad_id', 
        string='Usuarios que han leído'
    )


    def entregar_tarea(self):
        estudiante = self.env['agenda.estudiante'].search([('user_id', '=', self.env.user.id)], limit=1)
        actividad = self  # Actividad actual en la que el estudiante va a hacer la entrega

        if not estudiante or not actividad:
            raise ValidationError("No se encontró la actividad o el estudiante.")
    
        # Verificar si ya existe una entrega para este estudiante y actividad
        entrega_existente = self.env['agenda.actividad_entrega'].search([
            ('actividad_id', '=', actividad.id),
            ('estudiante_id', '=', estudiante.id)
        ], limit=1)
    
        if entrega_existente:
            # Si ya existe una entrega, abrir el registro existente para editar
            return {
                'type': 'ir.actions.act_window',
                'name': 'Entrega de Tarea',
                'res_model': 'agenda.actividad_entrega',
                'view_mode': 'form',
                'view_id': self.env.ref('agenda__electronica.view_form_actividad_entrega').id,
                'res_id': entrega_existente.id,
                'target': 'new',
                'context': {'default_actividad_id': actividad.id, 'default_estudiante_id': estudiante.id},
            }
        else:
            # Crear un nuevo registro en la base de datos con el valor inicial para el nombre del archivo
            entrega_vals = {
                'actividad_id': actividad.id,
                'estudiante_id': estudiante.id,
                'fecha_entrega': fields.Datetime.now(),
            }
            
            entrega = self.env['agenda.actividad_entrega'].create(entrega_vals)  # Esto guarda el registro en la base de datos
            
            # Subir el archivo a Dropbox y guardar la URL pública
            if entrega.archivo:  # Asumiendo que el campo del archivo se llama `archivo`
                entrega.subir_a_dropbox()
            # Abrir el registro recién creado en el modal
            return {
                'type': 'ir.actions.act_window',
                'name': 'Entrega de Tarea',
                'res_model': 'agenda.actividad_entrega',
                'view_mode': 'form',
                'view_id': self.env.ref('agenda__electronica.view_form_actividad_entrega').id,
                'res_id': entrega.id,
                'target': 'new',
                'context': {
                    'default_actividad_id': actividad.id,
                    'default_estudiante_id': estudiante.id,
                },
            }

    def ver_entregados(self):
        docente_role = self.env['roles.role'].search([('name', '=', 'Docentes')], limit=1)
        es_docente = self.env['roles.role'].search_count([
            ('id', '=', docente_role.id),
            ('user_ids', '=', self.env.user.id)
        ]) > 0
        
        if not es_docente:
            raise AccessError("No tienes permiso para ver esta información.")
        """Abre el modal con la lista de entregas de la actividad permitiendo editar el puntaje y descargar el archivo."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entregas de Actividad',
            'res_model': 'agenda.actividad_entrega',
            'view_mode': 'list',
            'view_id': self.env.ref('agenda__electronica.view_list_actividad_entrega_ver').id,
            'target': 'new',
            'domain': [('actividad_id', '=', self.id)],
            'context': {'create': False},  # Desactiva la creación de nuevas entregas desde el modal
        }


    def ver_leidos(self):
        docente_role = self.env['roles.role'].search([('name', '=', 'Docentes')], limit=1)
        es_docente = self.env['roles.role'].search_count([
            ('id', '=', docente_role.id),
            ('user_ids', '=', self.env.user.id)
        ]) > 0
        
        if not es_docente:
            raise AccessError("No tienes permiso para ver esta información.")
        """Abre el modal con la lista de usuarios que han leído el actividad."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Usuarios Leídos',
            'res_model': 'agenda.usuario_actividad',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('actividad_id', '=', self.id)],
            'context': {'create': False}, 
        }

    
    def action_guardar_y_volver(self):
        """Guardar el actividad y volver a la lista."""


        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'actividades',
            'res_model': 'agenda.actividad',
            'view_mode': 'list',
            'target': 'current',
            'domain': [('allowed_user_ids', 'in', [self.env.uid])]
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
        """Asignar automáticamente al docente actual como emisor y crear registros en usuario_actividad."""
        user = self.env.user
        archivo_data = vals.get('archivo')
        archivo_nombre = vals.get('archivo_nombre')
    
        # Buscar el docente asociado al usuario actual
        docente = self.env['agenda.docente'].search([('user_id', '=', user.id)], limit=1)
        if not docente:
            raise models.ValidationError("Solo un docente puede emitir un actividad.")
    
        # Verificar que el 'curso_docente_materia_id' ha sido proporcionado
        curso_docente_materia_id = vals.get('curso_docente_materia_id')
        if not curso_docente_materia_id:
            raise models.ValidationError("Debe seleccionar el curso y materia para el actividad.")
    
        curso_docente_materia = self.env['agenda.curso_docente_materia'].browse(curso_docente_materia_id)
        if curso_docente_materia.id_docente_materia.id_docente.id != docente.id:
            raise models.ValidationError("El curso y materia seleccionados no corresponden al docente actual.")
    
        # Asignar el curso_docente_materia_id al actividad
        vals['curso_docente_materia_id'] = curso_docente_materia.id
    
        # Crear el actividad
        actividad_new = super(Actividad, self).create(vals)
    
        # Continuar con el resto del método (por ejemplo, subir el archivo a Dropbox)
        if actividad_new.archivo and actividad_new.archivo_nombre:
            archivo_extesion = actividad_new.archivo_nombre 
            actividad_new.archivo_url = f"/web/content/{actividad_new._name}/{actividad_new.id}/{archivo_extesion}"
    
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
    
                actividad_new.public_url = download_url
    
            except Exception as e:
                raise Exception(f"Error al obtener o crear el enlace compartido en Dropbox: {e}")
        else:
            actividad_new.archivo_url = ""
    
        usuarios = self._obtener_usuarios_permitidos(actividad_new)
        # Crear registros en la tabla intermedia agenda.usuario_actividad
        for usuario in usuarios:
            self.env['agenda.usuario_actividad'].create({
                'usuario_id': usuario.id,
                'actividad_id': actividad_new.id,
                'enviado': True,
                'leido': False,
            })
    
        return actividad_new


    
    @api.depends('usuario_actividad_ids')
    def _compute_allowed_users(self):
        for record in self:
            record.allowed_user_ids = record.usuario_actividad_ids.mapped('usuario_id')


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

        # Usuarios permitidos: estudiantes, padres y el docente logeado
        usuarios = estudiantes.mapped('user_id') | padres.mapped('user_id') | docente.user_id
        
        return usuarios


    def ver_actividad(self):
        """Marcar como leído y abrir la vista detallada del actividad."""
        usuario = self.env.user
    
        # Buscar el registro correspondiente en la tabla usuario_actividad
        usuario_actividad = self.env['agenda.usuario_actividad'].search([
            ('actividad_id', '=', self.id),
            ('usuario_id', '=', usuario.id)
        ], limit=1)
    
        # Si el registro existe, marcarlo como leído
        if usuario_actividad:
            usuario_actividad.leido = True
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ver actividad',
            'res_model': 'agenda.actividad',
            'view_mode': 'form',
            'view_id': self.env.ref('agenda__electronica.view_html_actividad').id,
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
    


