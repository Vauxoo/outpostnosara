from odoo import models, fields


class PmsRoom(models.Model):
    _inherit = 'pms.room'

    lock_ids = fields.One2many('pms.lock', 'room_id', help="Room door locks.")

    def _clear_lock(self, usercode):
        for room in self:
            slots = room.lock_ids.slot_ids.filtered(lambda x: x.usercode == usercode)
            for slot in slots:
                slot.action_clear_user_code()

    def _set_lock(self, usercode):
        for room in self:
            for lock in room.lock_ids:
                if not lock.slot_ids:
                    lock.action_set_user_code(1, usercode)
                if lock.slot_ids.filtered(lambda x: x.usercode == usercode):
                    continue
                slot = lock.slot_ids.filtered(lambda x: not x.usercode)[:1]
                if slot:
                    slot.action_set_user_code(usercode)
                    continue
                last_slot_name = lock.slot_ids.sorted('name')[-1].name
                if last_slot_name < lock.max_slots:
                    lock.action_set_user_code(last_slot_name + 1, usercode)
