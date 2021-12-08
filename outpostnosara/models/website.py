from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def get_reservation(self):
        """ Return the last pre-reservation of the partner by:
                - session reservation_id
                - last pms.reservation.state = draft
                - Create new pre-reservation
            The pre-reservation is created with:
                - preconfirm: to set state = draft
                - overbooking: to set occupies_availability = false

        :return: last pre-reservation
        :rtype: pms.reservation
        """
        self.ensure_one()
        reservation_obj = self.env['pms.reservation'].with_company(request.website.company_id.id).sudo()
        partner = self.env.user.partner_id
        # There is only one property and it will be update in validate_reservation
        pms_property = self.env['pms.property'].sudo().search([], limit=1)
        reservation_id = request.session.get('reservation_id')

        # Test validity of the reservation_id
        if reservation_id:
            reservation = reservation_obj.browse(reservation_id)
            if reservation.exists().filtered(lambda r: r.state == 'draft'):
                return reservation

        # Search last validity of the reservation
        reservation = reservation_obj.search([
            ('state', '=', 'draft'),
            ('partner_id', '=', partner.id),
        ], limit=1)

        # Create a validity of the reservation
        if not reservation:
            reservation = self.env['pms.reservation'].create({
                'partner_id': partner.id,
                'pms_property_id': pms_property.id,
                'preconfirm': self._context.get('preconfirm', False),
                'overbooking': self._context.get('overbooking', True),
            })

        request.session['reservation_id'] = reservation.id
        return reservation
