# -*- coding: utf-8 -*-
{
    'name': "Agenda_Electronica",
    'summary': "Agenda escolar para comunicación entre padres, profesores y estudiantes.",
    'description': """
Agenda electrónica académica que permite la comunicación entre padres, estudiantes, y profesores. Proyecto para el segundo parcial de Ingeniería de Software 1 1-2024 FICCT
    """,
    'author': "Gustavo Camargo, Alex Roman y Carlos Romagera",
    'website': "https://www.uagrm.edu.bo/",
    'category': 'Education',
    'version': '0.1',

    'license': 'LGPL-3',  

    'depends': ['base', 'web', 'contacts', 'calendar', 'account'],


    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/roles_views.xml',
        'views/permisos_views.xml',
        'views/estudiantes_views.xml',
        'views/docente_views.xml',
        'views/administrativo_views.xml',
        'views/padreDeFamilia_views.xml',
        'views/comunicado_views.xml',
        'views/materias_views.xml',
        'views/cursos_views.xml',
        'views/notification_views.xml',
        'views/evento_views.xml',
        'views/actividades_views.xml',
        'views/module_installation_wizard_view.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'hooks.post_init_hook': 'execute_wizard_after_install',


    'installable': True,
    'application': True,
}
