from odoo import models, fields, api
from google.cloud import speech, storage
from google.oauth2 import service_account
import base64
import io
from pydub import AudioSegment
import requests
import openai
import logging
import time
import os
_logger = logging.getLogger(__name__)

class Evento(models.Model):
    _name = 'agenda.evento'
    _description = 'Evento'

    # Campos del modelo Evento
    tipo = fields.Selection([
        ('reunion', 'Reunión'),
        ('excursion', 'Excursión'),
        ('festival', 'Festival'),
        ('feria', 'Feria'),
        ('otro', 'Otro'),
    ], string="Tipo", required=True)
    
    descripcion = fields.Text(string="Descripción")
    fecha = fields.Datetime(string="Fecha", required=True)
    necesita_aceptacion = fields.Boolean(string="Necesita aceptar los términos")
    
    # Campos de archivo
    archivo_documento = fields.Binary(string="Documento adjunto")
    archivo_audio = fields.Binary(string="Audio adjunto")
    resumen = fields.Text(string="Resumen del audio")

    # Relación con estudiantes
    estudiante_ids = fields.One2many('agenda.evento_estudiante', 'evento_id', string='Estudiantes')
    
    # Relación con cursos
    curso_ids = fields.Many2many(
        'agenda.curso',
        string="Cursos",
        help="Selecciona los cursos para los que este evento será relevante"
    )
    
    @api.depends('curso_ids')
    def _compute_es_evento_docente(self):
        for record in self:
            docente = self.env['agenda.docente'].search([('user_id', '=', self.env.uid)], limit=1)
            if docente:
                # Verifica si hay al menos un curso en común entre curso_ids del evento y curso_ids del docente
                record.es_evento_docente = bool(set(record.curso_ids.ids) & set(docente.curso_ids.ids))
            else:
                record.es_evento_docente = False

    
    def action_abrir_subir_audio(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subir Audio',
            'res_model': 'agenda.evento',
            'view_mode': 'form',
            'view_id': self.env.ref('agenda__electronica.view_form_subir_audio').id,
            'target': 'new',
            'res_id': self.id,
        }

    # Método para abrir el modal de ver evento
    def action_abrir_ver_evento(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detalle del Evento',
            'res_model': 'agenda.evento',
            'view_mode': 'form',
            'view_id': self.env.ref('agenda__electronica.view_form_ver_evento').id,
            'target': 'new',
            'res_id': self.id,
        }
    
    def obtener_access_token(self):
        client_id = "geob75yb6u7h1zc"
        client_secret = "qxc0uucnyvs4q85"
        refresh_token = "bZTyFYYGNPEAAAAAAAAAAX1SF_PnxxcJ5rsoAl3RDmoNCxdijNFtxj_CnmeDvG71"
        
        url = "https://api.dropbox.com/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "OdooBot/1.0"}
        data = "grant_type=refresh_token&refresh_token={}&client_id={}&client_secret={}".format(refresh_token, client_id, client_secret)

        try:
            response = requests.post(url, headers=headers, data=data)
            _logger.info("Status Code de la solicitud de token: %s", response.status_code)
            _logger.info("Respuesta JSON de la solicitud de token: %s", response.json())
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                raise Exception(f"Error al obtener access token: {response.json()}")
        
        except Exception as e:
            _logger.error("Error durante la solicitud del token: %s", e)
            raise Exception(f"Error al obtener access token: {str(e)}")

    def subir_audio_a_gcs(self, archivo_audio, nombre_archivo):
        # Carga las credenciales y configura Google Cloud Storage
        cred_path = os.path.join(os.path.dirname(__file__), '../static/speech/credenciales-google.json')
        credenciales = service_account.Credentials.from_service_account_file(cred_path)
        storage_client = storage.Client(credentials=credenciales)
        
        bucket_name = 'agenda-electronica'  # Especifica tu bucket de GCS
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(nombre_archivo)

        try:
            # Decodifica el archivo de audio
            archivo_decodificado = base64.b64decode(archivo_audio)
            
            # Convierte el archivo a mono y 16000 Hz
            audio_segment = AudioSegment.from_file(io.BytesIO(archivo_decodificado), format="wav")
            audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
            
            # Exporta el audio ajustado a un objeto BytesIO
            audio_wav = io.BytesIO()
            audio_segment.export(audio_wav, format="wav")
            audio_wav.seek(0)

            # Sube el archivo convertido a GCS
            blob.upload_from_string(audio_wav.read(), content_type='audio/wav')
            gcs_uri = f'gs://{bucket_name}/{nombre_archivo}'
            _logger.info("Archivo subido a Google Cloud Storage: %s", gcs_uri)
            return gcs_uri
        except Exception as e:
            _logger.error("Error al subir el archivo a Google Cloud Storage: %s", e)
            raise Exception(f"Error al subir el archivo a Google Cloud Storage: {e}")

    def _configurar_api_openai(self):
        # Configura la clave de API de OpenAI
        openai.api_key = "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"

    def _generar_resumen_con_ia(self, transcripcion):
        self._configurar_api_openai()
        
        _logger.info("Iniciando generación de resumen de la transcripción con IA.")

        # Construcción del prompt para el resumen
        prompt = (
            f"Genera un resumen en formato de puntos numerados de los temas más importantes de la siguiente transcripción: {transcripcion}. "
            "Cada punto debe contener un tema principal o una conclusión importante discutida en la reunión, en el formato:\n"
            "1.- Primer punto importante\n"
            "2.- Segundo punto importante\n"
            "3.- Tercer punto importante\n"
            "Mantén los puntos claros y breves."
        )

        _logger.info("Prompt para OpenAI: %s", prompt)

        try:
            time.sleep(1)
            # Llama a la API de OpenAI para obtener el resumen
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            _logger.info("Respuesta completa de OpenAI: %s", response)

            # Accede a 'choices' y al 'content' de la respuesta de manera correcta
            if hasattr(response, 'choices') and response.choices:
                resumen_generado = response.choices[0].message.content.strip()
                
                _logger.info("Resumen generado por OpenAI: %s", resumen_generado)
                
                return resumen_generado
            else:
                _logger.warning("No se recibieron opciones en 'choices' en la respuesta de OpenAI")
                return "No se pudo generar el resumen de la transcripción."

        except Exception as e:
            _logger.error("Error al llamar a OpenAI: %s", e)
            return f"Error al generar el resumen: {e}"

    def action_generar_resumen(self):
        if self.archivo_audio:
            nombre_archivo = f'audio_evento_new_{self.id}.wav'
            bucket_name = 'agenda-electronica' 
            try:
                _logger.info("Iniciando subida de archivo a Google Cloud Storage...")
                gcs_uri = self.subir_audio_a_gcs(self.archivo_audio, nombre_archivo)
                _logger.info("Archivo subido exitosamente. Obteniendo transcripción...")

                # Configura las credenciales de Google Speech
                cred_path = os.path.join(os.path.dirname(__file__), '../static/speech/credenciales-google.json')
                credenciales = service_account.Credentials.from_service_account_file(cred_path)
                client = speech.SpeechClient(credentials=credenciales)

                # Configuración para el reconocimiento de audio
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,  # Ahora coincide con el archivo de audio
                    language_code="es-ES"
                )
                audio = speech.RecognitionAudio(uri=gcs_uri)

                # Usa long_running_recognize para archivos largos
                _logger.info("Usando long_running_recognize con GCS URI...")
                operation = client.long_running_recognize(config=config, audio=audio)
                response = operation.result(timeout=300)  # Ajusta el tiempo de espera según sea necesario

                if not response.results:
                    _logger.warning("No se recibieron resultados de la transcripción.")
                    self.resumen = "No se pudo transcribir el audio."
                else:
                    transcripcion = ' '.join([result.alternatives[0].transcript for result in response.results])
                    _logger.info("Transcripción obtenida exitosamente.")
                    if transcripcion:
                        # Genera un resumen de la transcripción usando IA
                        resumen = self._generar_resumen_con_ia(transcripcion)
                        self.resumen = resumen
                    else:
                        self.resumen = "No se pudo obtener una transcripción del audio."

                # Opcional: Elimina el archivo de GCS después de la transcripción
                blob = storage.Client(credentials=credenciales).bucket(bucket_name).blob(nombre_archivo)
                blob.delete()
                _logger.info("Archivo eliminado de Google Cloud Storage.")

            except Exception as e:
                _logger.error("Error durante la generación de resumen: %s", e)
                self.resumen = f"Error al procesar el archivo de audio: {e}\n"

    @api.model
    def create(self, vals):
        record = super(Evento, self).create(vals)
        record._crear_relaciones_evento_estudiante()
        return record

    def write(self, vals):
        res = super(Evento, self).write(vals)
        if 'curso_ids' in vals:
            self._crear_relaciones_evento_estudiante()
        return res

    def _crear_relaciones_evento_estudiante(self):
        """Crea las relaciones en agenda.evento_estudiante y notificaciones para cada estudiante y sus padres."""
        if self.curso_ids:
            # Obtener todos los estudiantes de los cursos seleccionados
            estudiantes = self.env['agenda.estudiante'].search([
                ('curso_id', 'in', self.curso_ids.ids)
            ])
            # Actualizar el campo estudiante_ids para reflejar los estudiantes relacionados
            self.estudiante_ids = [(6, 0, estudiantes.ids)]
            
            # Eliminar relaciones existentes para evitar duplicados
            self.env['agenda.evento_estudiante'].search([('evento_id', '=', self.id)]).unlink()
            
            # Crear los registros en agenda.evento_estudiante y notificaciones para cada estudiante y sus padres
            for estudiante in estudiantes:
                # Crear relación en agenda.evento_estudiante
                self.env['agenda.evento_estudiante'].create({
                    'evento_id': self.id,
                    'estudiante_id': estudiante.id,
                    'leido': False,
                    'confirmacion': False,
                    'asistencia': False,
                })

                # Crear una notificación para el estudiante
                self.env['agenda.notificacion'].create({
                    'type': 'nuevo_evento',
                    'data': f"Se ha asignado un nuevo evento al estudiante {estudiante.name}",
                    'user_id': estudiante.user_id.id,  
                })

                # Obtener los padres de familia asociados al estudiante
                padres = self.env['agenda.padre_familia'].search([
                    ('estudiante_ids', 'in', estudiante.id)
                ])
                for padre in padres:
                    # Crear una notificación para cada padre
                    self.env['agenda.notificacion'].create({
                        'type': 'nuevo_evento',
                        'data': f"Se ha asignado un nuevo evento al estudiante {estudiante.name} del que eres responsable",
                        'user_id': padre.user_id.id,
                    })

    def action_registrar_asistencia(self):
        """Abrir la vista para registrar asistencia de los estudiantes asociados al evento."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Asistencia',
            'res_model': 'agenda.evento_estudiante',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('evento_id', '=', self.id)],  # Filtra los registros relacionados con el evento actual
        }

        
    def action_guardar_y_volver(self):
        """Guardar el evento y volver a la lista."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Eventos',
            'res_model': 'agenda.evento',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_open_form(self):
        """Abrir el formulario para editar el evento."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Evento',
            'res_model': 'agenda.evento',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'hide_buttons': True},
        }
        
    