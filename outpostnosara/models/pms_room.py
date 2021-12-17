from odoo import models, fields


class PmsRoom(models.Model):
    _inherit = 'pms.room'

    lock_id = fields.Many2one('pms.lock', string="Room door lock")

    def _clear_lock(self, usercode):
        for room in self:
            slot = room.lock_id.slot_ids.filtered(lambda x: x.usercode == usercode)
            slot.action_clear_user_code()

    def _set_lock(self, usercode):
        for room in self:
            slot = room.lock_id.slot_ids.filtered(lambda x: not x.usercode)[:1]
            slot.action_clear_user_code(slot.name, usercode)
