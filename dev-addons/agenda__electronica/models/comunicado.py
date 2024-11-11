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

    allowed_user_ids = fields.Many2many(
        'res.users',
        string='Usuarios Permitidos',
        compute='_compute_allowed_user_ids',
        store=True
    )



    matching_user = fields.Boolean(string="Usuario coincide", compute="_compute_matching_user")


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

    curso_ids = fields.Many2many(
        'agenda.curso', 
        string='Enviar a Cursos'
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
            'view_id': self.env.ref('agenda__electronica.view_usuarios_leidos').id,
            'target': 'new',
            'domain': [('comunicado_id', '=', self.id)],
            'context': {'create': False}, 
        }

    
    def action_guardar_y_volver(self):
        """Guardar el comunicado y volver a la lista."""
        domain = [('allowed_user_ids', 'in', [self.env.uid])]

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


        if comunicado.curso_ids:
            estudiantes = self.env['agenda.estudiante'].search([
                ('curso_id', 'in', comunicado.curso_ids.ids)
            ])
            usuarios |= estudiantes.mapped('user_id')  # Asegúrate de tener un campo `user_id` en el modelo `Estudiante`


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


    @api.depends('curso_ids', 'rol_ids')
    def _compute_matching_user(self):
        current_user = self.env.user
        for record in self:
            # Verificar si el usuario está en los roles seleccionados
            roles_match = any(current_user in role.user_ids for role in record.rol_ids)
            # Verificar si el usuario está en los cursos seleccionados
            courses_match = any(student.user_id == current_user for course in record.curso_ids for student in course.estudiante_ids)

            # Coincidencia para padres de estudiantes en los cursos
            parent_match = any(
                current_user == padre.user_id 
                for course in record.curso_ids 
                for student in course.estudiante_ids 
                for padre in self.env['agenda.padre_familia'].search([('estudiante_ids', 'in', [student.id])])
            )


            teacher_match = any(
                current_user == docente.user_id
                for course in record.curso_ids
                for docente_materia in self.env['agenda.curso_docente_materia'].search([('id_curso', '=', [course.id])])
                for docente in docente_materia.id_docente_materia.id_docente
            )
            print(f"Teacher match for user {current_user.name}: {teacher_match}")

            # Aplicar lógica condicional:
            if record.rol_ids and record.curso_ids:
                # Si hay roles y cursos seleccionados, ambos deben coincidir
                record.matching_user = roles_match and (courses_match or parent_match or teacher_match)
            elif record.rol_ids:
                # Si sólo hay roles seleccionados, considerar sólo los roles
                record.matching_user = roles_match
            elif record.curso_ids:
                # Si sólo hay cursos seleccionados, considerar sólo los cursos
                record.matching_user = courses_match or parent_match or teacher_match
            else:
                # Si no hay roles ni cursos seleccionados, hacer visible para todos
                record.matching_user = True  


    @api.depends('rol_ids', 'curso_ids')
    def _compute_allowed_user_ids(self):
        for record in self:
            # Conjuntos de usuarios
            role_users = record.rol_ids.mapped('user_ids') if record.rol_ids else self.env['res.users']
            allowed_users = self.env['res.users'].browse()
            
            # Si hay cursos seleccionados, obtener usuarios asociados
            if record.curso_ids:
                # Estudiantes en los cursos
                students = record.curso_ids.mapped('estudiante_ids')
                student_users = students.mapped('user_id')
                
                # Padres de los estudiantes
                parent_users = students.mapped('padre_familia_ids.user_id')
                
                # Docentes de los cursos
                docentes = record.curso_ids.mapped('curso_docente_materia_ids.id_docente_materia.id_docente')
                teacher_users = docentes.mapped('user_id')
            else:
                # Si no hay cursos, conjuntos vacíos
                student_users = self.env['res.users']
                parent_users = self.env['res.users']
                teacher_users = self.env['res.users']
            
            # Lógica condicional basada en la presencia de roles y cursos
            if record.rol_ids and record.curso_ids:
                # Usuarios que están en roles y asociados a los cursos
                # Intersección de usuarios de roles con estudiantes, padres y docentes
                allowed_users |= role_users & student_users
                allowed_users |= role_users & parent_users
                allowed_users |= role_users & teacher_users
            elif record.rol_ids:
                # Solo roles seleccionados
                allowed_users = role_users
            elif record.curso_ids:
                # Solo cursos seleccionados
                allowed_users = student_users | parent_users | teacher_users
            else:
                # Sin roles ni cursos, todos los usuarios
                allowed_users = self.env['res.users'].search([])
            
            # Asignar usuarios permitidos
            record.allowed_user_ids = allowed_users
