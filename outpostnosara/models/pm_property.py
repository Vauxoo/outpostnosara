import pytz

from odoo import models


class PmsProperty(models.Model):
    _inherit = 'pms.property'

    def date_property_timezone(self, dtimezone):
        """Overwritten this because the following error when user does not have timezone set
        AttributeError: 'bool' object has no attribute 'upper'
        """
        self.ensure_one()
        # Here is the change, also validating user self.env.user.tz
        if self.env.user and self.env.user.tz:
            tz_property = self.tz
            dtimezone = pytz.timezone(tz_property).localize(dtimezone)
            dtimezone = dtimezone.replace(tzinfo=None)
            dtimezone = pytz.timezone(self.env.user.tz).localize(dtimezone)
            dtimezone = dtimezone.astimezone(pytz.utc)
            dtimezone = dtimezone.replace(tzinfo=None)
        return dtimezone
