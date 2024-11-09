from odoo import models, fields, api
from pydub import AudioSegment
import speech_recognition as sr
from io import BytesIO
import base64


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

    # Método para procesar el audio y generar el resumen
    def action_generar_resumen(self):
        if self.archivo_audio:
            # Decodifica el archivo de audio de base64 a BytesIO
            audio_data = base64.b64decode(self.archivo_audio)
            audio_file = BytesIO(audio_data)

            # Convierte el archivo de audio a WAV si es necesario
            try:
                # Intenta cargar el archivo de audio en pydub
                audio_segment = AudioSegment.from_file(audio_file)
                # Convierte el archivo a WAV y guarda en BytesIO
                wav_io = BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)  # Regresa al inicio del archivo WAV

                # Crear el objeto de reconocimiento de voz
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_io) as source:
                    audio = recognizer.record(source)
                    # Transcribir el audio a texto en español
                    texto_transcrito = recognizer.recognize_google(audio, language='es-ES')
                    self.resumen = texto_transcrito
            except sr.UnknownValueError:
                self.resumen = "No se pudo entender el audio."
            except sr.RequestError:
                self.resumen = "Error en la solicitud de reconocimiento de voz."
            except Exception as e:
                self.resumen = f"Error al procesar el audio: {str(e)}"


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
        """Crea las relaciones en agenda.evento_estudiante."""
        if self.curso_ids:
            # Obtener todos los estudiantes de los cursos seleccionados
            estudiantes = self.env['agenda.estudiante'].search([
                ('curso_id', 'in', self.curso_ids.ids)
            ])
            # Actualizar el campo estudiante_ids para reflejar los estudiantes relacionados
            self.estudiante_ids = [(6, 0, estudiantes.ids)]
            
            # Eliminar relaciones existentes para evitar duplicados
            self.env['agenda.evento_estudiante'].search([('evento_id', '=', self.id)]).unlink()
            
            # Crear los registros en agenda.evento_estudiante para cada estudiante
            for estudiante in estudiantes:
                self.env['agenda.evento_estudiante'].create({
                    'evento_id': self.id,
                    'estudiante_id': estudiante.id,
                    'leido': False,
                    'confirmacion': False,
                    'asistencia': False,
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
        
    