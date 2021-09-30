# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Instance Creator',
    'summary': '''
    Instance creator for outpostnosara. This is the app.
    ''',
    'author': 'Vauxoo',
    'website': 'https://www.vauxoo.com',
    'license': 'LGPL-3',
    'category': 'Installer',
    'version': '14.0.1.0.0',
    'depends': [
        'l10n_cr',
        'l10n_cr_edi',
    ],
    'test': [
    ],
    'data': [
        'data/res_company_data.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
