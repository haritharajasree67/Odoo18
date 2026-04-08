from odoo import http
from odoo.http import request

class ChequeAttributeController(http.Controller):

    @http.route('/cheque/configure_attributes', type='http', auth='user', website=True)
    def configure_attributes_page(self, cheque_id=None):
        print('mmmmmmmmmmmmmmmmmmmmmmm')
        if not cheque_id:
            return request.redirect('/error_page')
        cheque = request.env['bank.cheque'].sudo().browse(int(cheque_id))
        cheque_attributes = request.env['cheque.attribute'].sudo().search([('cheque_id', '=', cheque.id)])
        return request.render('dynamic_bank_cheque.cheque_configure_template', {
            'cheques': cheque_attributes,
            'image': cheque.cheque_image,
        })

    @http.route('/update_cheque_attribute', type='json', auth='user')
    def update_cheque_attribute(self, **kwargs):
        print("Route hit: update_cheque_attribute")

        # Data comes from JSON RPC
        attribute_id = kwargs.get('attribute_id')
        x1 = kwargs.get('x1')
        y1 = kwargs.get('y1')
        x2 = kwargs.get('x2')
        y2 = kwargs.get('y2')

        print(f"Received data: {kwargs}")

        if not attribute_id:
            return {'status': 'error', 'message': 'No attribute_id provided'}

        cheque_attribute = request.env['cheque.attribute'].sudo().browse(int(attribute_id))
        print(cheque_attribute, 'ppppppppppppppppp')

        if cheque_attribute.exists():
            cheque_attribute.write({
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2),
            })
            return {'status': 'success'}

        return {'status': 'error', 'message': 'Record not found'}

    @http.route('/save_all_cheque_positions', type='http', auth='user', methods=['POST'])
    def save_all_cheque_positions(self, positions):
        for pos in positions:
            attribute = request.env['cheque.attribute'].sudo().browse(pos['id'])
            if attribute.exists():
                attribute.write({
                    'x1_position': int(pos['x1']),
                    'y1_position': int(pos['y1']),
                    'x2_position': int(pos['x2']),
                    'y2_position': int(pos['y2']),
                })
        return {'status': 'success'}
