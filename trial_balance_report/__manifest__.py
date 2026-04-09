# -*- coding: utf-8 -*-
{
    'name': 'Dynamic Trial Balance Report',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Dynamic Trial Balance Report grouped by Account Group with expandable rows',
    'description': """
        Dynamic Trial Balance Report for Odoo 18
        =========================================
        Features:
        - Grouped by Account Group with expand/collapse
        - Initial Balance, This Financial Year, Ending Balance columns
        - Date range filters
        - Export to XLSX and PDF
        - Real-time dynamic loading
    """,
    'author': 'Custom',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/trial_balance_wizard_views.xml',
        # 'views/trial_balance_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trial_balance_report/static/src/css/trial_balance.css',
            'trial_balance_report/static/src/js/trial_balance.js',
            'trial_balance_report/static/src/xml/trial_balance.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
