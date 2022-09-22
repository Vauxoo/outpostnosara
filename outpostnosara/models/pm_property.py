import pytz
import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PmsProperty(models.Model):
    _inherit = 'pms.property'

    default_arrival_hour = fields.Char(default="12:00")
    default_departure_hour = fields.Char(default="14:00")
    wifi_name = fields.Char(help="Name of the WiFi Network")
    wifi_password = fields.Char(help="Pasword of the WiFi Network")

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

    @api.depends_context(
        "checkin",
        "checkout",
        "arrival_hour",
        "departure_hour",
        "room_type_id",
        "ubication_id",
        "capacity",
        "amenity_ids",
        "pricelist_id",
        "current_lines",
    )
    def _compute_free_room_ids(self):
        '''Overwritten in order to ensure checkin is a datetime, so, the free rooms are checked using time too'''
        checkin = self._context["checkin"]
        checkout = self._context["checkout"]

        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(checkin, DEFAULT_SERVER_DATE_FORMAT)
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(checkout, DEFAULT_SERVER_DATE_FORMAT)

        current_lines = self.env.context.get("current_lines", [])
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]

        pricelist_id = self.env.context.get("pricelist_id")

        for pms_property in self:
            # This and get_rooms_not_avail are the real methods that computes the rooms
            free_rooms = pms_property.get_real_free_rooms(checkin, checkout, current_lines)
            if pricelist_id:
                free_rooms = self._consider_price_list(checkin, checkout, pms_property, pricelist_id, free_rooms)

            pms_property.free_room_ids = free_rooms

    def _consider_price_list(self, checkin, checkout, pms_property, pricelist_id, free_rooms):
        """Technical method to reduce complexity from the original pms code."""
        # TODO: Original Module comment: only closed_departure take account checkout date!.
        # TODO: OUTPOST: This code block was not improved to work with datetime, not necessary for now
        pricelist = self.env["product.pricelist"].browse(pricelist_id)
        plan = pricelist.availability_plan_id
        if not plan:
            return free_rooms
        domain_rules = [
            ("date", ">=", checkin),
            ("date", "<=", checkout),
            ("pms_property_id", "=", pms_property.id),
            ("availability_plan_id", "=", plan.id),
        ]
        room_type_id = self.env.context.get("room_type_id", False)
        if room_type_id:
            domain_rules.append(("room_type_id", "=", room_type_id))
        rule_items = self.env["pms.availability.plan.rule"].search(domain_rules)
        room_types_to_remove = [
            item.room_type_id.id for item in rule_items if plan.any_rule_applies(checkin, checkout, item)]
        free_rooms = free_rooms.filtered(lambda x: x.room_type_id.id not in room_types_to_remove)

    def get_real_free_rooms(self, checkin, checkout, current_lines=False):
        """OVERWRITTEN"""
        self.ensure_one()
        pms_room = self.env["pms.room"]
        pms_avail = self.env["pms.availability"]
        target_room_domain = [("pms_property_id", "=", self.id)]

        room_type_id = self.env.context.get("room_type_id")
        if room_type_id:
            target_room_domain.append(("room_type_id", "=", room_type_id))

        capacity = self.env.context.get("capacity")
        if capacity:
            target_room_domain.append(("capacity", ">=", capacity))

        ubication_id = self.env.context.get("ubication_id")
        if ubication_id:
            target_room_domain.append(("ubication_id", "=", ubication_id))

        target_rooms = pms_room.search(target_room_domain)

        amenity_ids = self.env.context.get("amenity_ids")
        if amenity_ids:
            if not isinstance(amenity_ids, list):
                amenity_ids = [amenity_ids]
            target_rooms = target_rooms.filtered(lambda r: len(set(amenity_ids) - set(r.room_amenity_ids.ids)) == 0)

        # Give priority to those rooms that are not being used this day
        rooms_not_avail_ids = pms_avail.get_rooms_not_avail(
            checkin=checkin,
            checkout=checkout,
            room_ids=target_rooms.ids,
            pms_property_id=self.id,
            current_lines=current_lines or [],
        )

        domain_rooms = [("id", "in", target_rooms.ids)]

        if not rooms_not_avail_ids:
            # All rooms are available
            return pms_room.search(domain_rooms)

        domain_rooms.append(("id", "not in", rooms_not_avail_ids))
        free_rooms = pms_room.search(domain_rooms)

        if free_rooms:
            return free_rooms

        # Repeat the search but now using datetime dates
        rooms_not_avail_ids = pms_avail.with_context(use_datetimes=True).get_rooms_not_avail(
            checkin=checkin,
            checkout=checkout,
            room_ids=target_rooms.ids,
            pms_property_id=self.id,
            current_lines=current_lines or [],
        )
        domain_rooms = [("id", "in", target_rooms.ids)]
        if rooms_not_avail_ids:
            domain_rooms.append(("id", "not in", rooms_not_avail_ids))
        return self.env["pms.room"].search(domain_rooms)
