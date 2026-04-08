{
    'name': 'Available Quantity in Sales',
    'version': '18.0.1.0.0',
    'summary': 'On hand Quantity of Product in Quotation',
    'category': 'Sale',
    'depends': ['sale','purchase'],
    'data': [
        'views/sale_order.xml',
        'views/sale_access.xml',


    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}