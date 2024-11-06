from odoo import models, fields, api
from datetime import datetime
import firebase_admin
from firebase_admin import messaging, credentials
import os
import logging

_logger = logging.getLogger(__name__)
class AgendaNotificacion(models.Model):
    _name = 'agenda.notificacion'
    _description = 'Notificación de Agenda'

    type = fields.Selection(
        selection=[
            ('nuevo_comunicado', 'Nuevo Comunicado'),
            ('nueva_tarea', 'Nueva Tarea'),
            ('nueva_entrega', 'Nueva Entrega')
        ],
        string='Tipo de Notificación',
        required=True
    )
    data = fields.Text(string='Datos')
    read_at = fields.Datetime(string='Fecha de Lectura', readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario')

    def mark_as_read(self):
        """Marcar la notificación como leída."""
        self.read_at = datetime.now()

    # Inicializa Firebase Admin SDK solo una vez
    if not firebase_admin._apps:
        cred_path = os.path.join(
                os.path.dirname(__file__), '../static/firebase/firebase-adminsdk.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    @api.model
    def create(self, vals):
        record = super(AgendaNotificacion, self).create(vals)

        # Configura el contenido de la notificación
        notification_title = "Nueva Notificación"
        notification_body = f"Tienes una {dict(self._fields['type'].selection).get(vals.get('type'))}"

        for token_record in record.user_id.device_token_ids:
            user_token = token_record.device_token
            if user_token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=notification_title,
                        body=notification_body,
                    ),
                    data={"data": record.data},
                    token=user_token,
                )

                # Envía el mensaje
                response = messaging.send(message)
                _logger.info("Firebase notification sent to %s: %s", user_token, response)

        return record

    def action_guardar_y_volver(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Notificaciones',
            'view_mode': 'list',
            'res_model': 'agenda.notificacion',
            'target': 'current',
        }
