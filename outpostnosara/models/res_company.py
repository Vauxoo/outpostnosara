from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_default_l10n_cr_edi_economic_activity(self):
        default_activity = self.env.ref('l10n_cr_edi.company_activity_701002', raise_if_not_found=False)
        if default_activity and default_activity in self.l10n_cr_edi_economic_activity_ids:
            return default_activity.id
        return self.l10n_cr_edi_economic_activity_ids[:1].id
