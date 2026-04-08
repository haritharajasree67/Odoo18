{
    'name': "POS Backdate Entry",
    'version': '18.0.1.0.0',
    'summary': 'POS Backdate Entry',
    'category': 'Point of Sale',
    'description': """ This module allows to abackdate the POS order and session close.""",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config.xml',
        'views/session_report.xml',


    ],

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}