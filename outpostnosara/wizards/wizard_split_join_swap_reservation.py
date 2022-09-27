from odoo import api, models, _
from odoo.exceptions import UserError


class ReservationSplitJoinSwapWizard(models.TransientModel):
    _inherit = "pms.reservation.split.join.swap.wizard"

    @api.depends("checkin", "checkout", "room_source", "room_target")
    def _compute_reservation_ids(self):
        """ OVERWRITTEN
            This compute was modified because originally it makes a tour of the reservation lines, which causes the
            search process to be very slow, now the search is carried out directly through the reservation, obtaining
            an improvement in the filter.
        """
        for record in self:
            if record.checkin and record.checkout:
                room_ids = [record.room_source.id]
                if record.room_target:
                    room_ids.append(record.room_target.id)
                domain = [
                    ("preferred_room_id", "in", room_ids),
                    ("rooms", "!=", False),
                    ("state", "!=", "cancel"),
                    ("checkin", "<=", record.checkin), ("checkout", ">=", record.checkout),
                ]
                reservations = (self.env["pms.reservation"].search(domain).sorted("rooms"))
                record.reservation_ids = reservations
            else:
                record.reservation_ids = False

    @api.model
    def reservations_swap(self, checkin, checkout, source, target):
        """ OVERWRITTEN
            This method was modified because the swap process went through the lines to update one by one, making the
            process very slow, now it is done in a direct block by the reservation, making it more optimal.
        """
        source = self.env['pms.room'].browse(source)
        target = self.env['pms.room'].browse(target)
        reservations = self.env["pms.reservation"].search(
            [("checkin", ">=", checkin), ("checkout", "<=", checkout)]
        )
        line_room_source = self.env["pms.reservation.line"].search(
            [("room_id", "=", source.id), ("reservation_id", "in", reservations.ids)]
        )
        if not line_room_source:
            raise UserError(_("There's no reservations lines with provided room"))

        if not target:
            raise UserError(_("There's no selected room target"))

        line_room_target = self.env["pms.reservation.line"].search(
            [("reservation_id", "in", reservations.ids), ("room_id", "=", target.id)]
        )
        # Update the reservation lines making the room swap faster.
        self.env.cr.execute(
            "UPDATE pms_reservation_line SET room_id = %s, occupies_availability = false WHERE id in %s",
            [target.id, tuple(line_room_source.ids)])
        self.env.cr.execute(
            "UPDATE pms_reservation SET preferred_room_id = %s, room_type_id = %s WHERE id in %s",
            [target.id, target.room_type_id.id, tuple(line_room_source.mapped('reservation_id').ids)])
        if line_room_target:
            self.env.cr.execute(
                "UPDATE pms_reservation_line SET room_id = %s, occupies_availability = false WHERE id in %s",
                [source.id, tuple(line_room_target.ids)])
            self.env.cr.execute(
                "UPDATE pms_reservation SET preferred_room_id = %s, room_type_id = %s WHERE id in %s",
                [source.id, source.room_type_id.id, tuple(line_room_target.mapped('reservation_id').ids)])
        self.flush()
        reservation_lines = line_room_source | line_room_target
        reservation_lines._compute_room_id()

    @api.depends_context("default_operation")
    @api.depends("checkin", "checkout", "room_source", "operation")
    def _compute_allowed_rooms_target(self):
        """ OVERWRITTEN
            This method was modified to allow swapping with a room that does not have a reservation.
        """
        for record in self:
            record.allowed_rooms_target = False
            record.room_target = False
            if record.checkin and record.checkout:
                domain = [("capacity", ">=", record.reservation_id.adults)]
                if record.room_source:
                    domain.append(("id", "!=", record.room_source.id))
                # Here it allows to select a target that does not have a reservation.
                if record.operation != "swap":
                    pms_property = record.reservation_id.pms_property_id
                    pms_property = pms_property.with_context(
                        checkin=record.checkin,
                        checkout=record.checkout,
                        room_type_id=False,  # Allows to choose any available room
                        current_lines=record.reservation_id.reservation_line_ids.ids,
                        pricelist_id=record.reservation_id.pricelist_id.id,
                    )
                    rooms_available = pms_property.free_room_ids
                    domain.extend(
                        [
                            ("id", "in", rooms_available.ids),
                        ]
                    )
                record.allowed_rooms_target = self.env["pms.room"].search(domain)
