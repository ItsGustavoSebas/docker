# -*- coding: utf-8 -*-
{
    'name': "Agenda_Electronica",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
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
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
}

