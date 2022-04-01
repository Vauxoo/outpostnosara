# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Theme Nosara',
    'summary': 'Nosara Official Theme',
    'version': '14.0.1.0.6',
    'author': 'Vauxoo',
    'website': 'https://www.vauxoo.com',
    'license': 'LGPL-3',
    'data': [
        # views
        'views/assets.xml',
        'views/images_library.xml',
        # Templates
        'views/templates/helpdesk_templates.xml',
        'views/templates/layout_templates.xml',
        'views/templates/snippets.xml',
    ],
    'demo': [
        'demo/theme_demo.xml',
    ],
    'category': 'Theme/Creative',
    'depends': [
        'website_helpdesk_form',
    ],
    'images': [
        'static/description/theme_nosara_screenshot.jpg',
    ],
    'installable': True,
}
