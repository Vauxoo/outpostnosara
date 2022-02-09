# Copyright 2022 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License OPL-1 (https://www.odoo.com/documentation/user/13.0/legal/licenses/licenses.html).
{
    'name': 'Payment Immediate Credit',
    'summary': '''
    Allows payments without pay at the moment. The transactions would be on Pending State
    ''',
    'author': 'Vauxoo',
    'website': 'http://www.vauxoo.com',
    'license': 'OPL-1',
    'category': 'Installer',
    'version': '14.0.0.0.0',
    'price': 40,
    'currency': 'USD',
    'depends': [
        'sale_management',
        'website_sale'
    ],
    'data': [
        'views/assets.xml',
        'views/payment_form_views.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    "demo": [],
    'qweb': [],
    'images': [],
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': True,
}
