# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class ThemeNosara(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_nosara_post_copy(self, mod):
        # Shopping cart
        self.disable_view('website_sale.template_header_default')
        # Footer Language Selector
        self.disable_view('portal.footer_language_selector')
        # Unnecessary classes
        self.disable_view('website.assets_frontend_compatibility_for_12_0')
