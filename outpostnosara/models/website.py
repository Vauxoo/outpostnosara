from odoo import _, models
from odoo.http import request
from odoo.exceptions import ValidationError


class Website(models.Model):
    _inherit = 'website'

    def get_reservation(self, reservation_key, invoice_create=None):
        """ Return the last pre-reservation of the partner by:
                - session reservation_id
                - last pms.reservation.state = draft
                - Create new pre-reservation
            The pre-reservation is created with:
                - preconfirm: to set state = draft
                - overbooking: to set occupies_availability = false
            And We have to reset room_id the room won't update

        :return: last pre-reservation
        :rtype: pms.reservation
        """
        self.ensure_one()
        user = self.env.user
        if not user.pms_property_id or not user.pms_property_ids:
            raise ValidationError(_("Please, set a property for the user"))

        reservation_obj = self.env['pms.reservation'].with_company(request.website.company_id.id).sudo()
        partner = user.partner_id
        # Default Property
        pms_property = user.pms_property_id
        reservation_id = request.session.get(reservation_key)

        # Test validity of the reservation_id
        if reservation_id:
            reservation = reservation_obj.browse(reservation_id)
            if reservation.exists().filtered(lambda r: r.state == 'draft'):
                # We have to reset in this specific order or the room won't update
                if not invoice_create:
                    reservation.write({
                        'reservation_line_ids': False,
                        'preferred_room_id': False,
                    })
                return reservation

        # Search last validity of the reservation
        podcast_room_id = self.env.ref('outpost.podcast_studio_room_type')
        domain = [
            ('state', '=', 'draft'),
            ('partner_id', '=', partner.id)
        ]
        if reservation_key == 'reservation_id':
            domain.append(('room_type_id', '!=', podcast_room_id.id))
        else:
            domain.append(('room_type_id', '=', podcast_room_id.id))
        reservation = reservation_obj.search(domain, limit=1)

        # Create a validity of the reservation
        if not reservation:
            reservation = reservation_obj.create({
                'partner_id': partner.id,
                'pms_property_id': pms_property.id,
                'preconfirm': self._context.get('preconfirm', False),
                'overbooking': self._context.get('overbooking', True),
            })

        # We have to reset in this specific order or the room won't update
        reservation.write({
            'reservation_line_ids': False,
            'preferred_room_id': False,
        })

        request.session[reservation_key] = reservation.id
        return reservation
