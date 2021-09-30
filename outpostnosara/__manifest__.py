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
    'version': '14.0.1.0.1',
    'depends': [
        'l10n_cr',
        'l10n_cr_edi',
        'account_accountant',
        'helpdesk',
        'hr_holidays',
        'iot',
        'mass_mailing',
        'point_of_sale',
        'purchase',
        'sale_management',
        'sale_subscription',
        'stock',
        'timesheet_grid',
        'website_sale',
        'website_calendar',
        'report_xlsx_helper',
        'pms_housekeeping',
        'pms_rooming_xls',
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
