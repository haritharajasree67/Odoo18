{
    'name': 'StockPulse: Forecast & Alerts',
    'summary': 'StockPulse: Forecast & Alerts',
    'version': '18.0.1.0.0',
    'category': 'Sale',
    'description': """ StockPulse: Forecast & Alerts""",
    'depends': ['sale_management','stock','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/manu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smart_inventory_forecast/static/src/js/dashboard.js',
            'smart_inventory_forecast/static/src/xml/dashboard.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',


}