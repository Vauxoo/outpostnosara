import base64
from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_resource_path


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    install_theme(env)
    add_logo(env)


def install_theme(env):
    theme = env.ref('base.module_theme_nosara')
    website = env.ref('website.default_website')
    theme._theme_load(website)


def add_logo(env):
    website = env.ref('website.default_website')
    try:
        path = get_resource_path('outpostnosara', 'static/img', 'logo.svg')
        website.logo = base64.b64encode(open(path, 'rb').read()) if path else False
    except (IOError, OSError):
        website.logo = False
