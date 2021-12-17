import pytz

from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = 'pms.property'

    default_arrival_hour = fields.Char(default="12:00")
    default_departure_hour = fields.Char(default="14:00")

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
