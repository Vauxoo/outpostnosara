
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    housekeeping_task = fields.Integer(string='Housekeeping Tasks', compute='_compute_housekeeping_task')
    project_task = fields.Integer(string='Project Tasks', compute='_compute_project_task')
    maintenance_task = fields.Integer(string='Maintenance Tasks', compute='_compute_maintenance_task')

    def _compute_housekeeping_task(self):
        for rec in self:
            housekeeping_task = self.env['pms.housekeeping'].search_count([('employee_id', '=', rec.id)])
            rec.housekeeping_task = housekeeping_task

    def _compute_maintenance_task(self):
        for rec in self:
            maintenance_task = self.env['maintenance.request'].search_count([('user_id', '=', rec.user_id.id)])
            rec.maintenance_task = maintenance_task

    def _compute_project_task(self):
        for rec in self:
            project_task = self.env['account.analytic.line'].search_count([('employee_id', '=', rec.id)])
            rec.project_task = project_task

    def activities_housekeeping(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'housekeeping',
            'res_model': 'pms.housekeeping',
            'view_mode': 'tree,form',
            'domain': [('employee_id', "=", self.id)],
            'target': 'current',
        }

    def activities_project(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'project',
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'domain': [('employee_id', "=", self.id)],
            'target': 'current',
        }

    def activities_maintenance(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'project',
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
            'domain': [('user_id', "=", self.user_id.id)],
            'target': 'current',
        }
