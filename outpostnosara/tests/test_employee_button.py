from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestButtonEmployee(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Jon Doe',
            'login': 'doe_user',
            'email': 'jon_doe@yourcompany.com',

        })
        self.employee = self.env['hr.employee'].create({
            'user_id': self.user.id,
        })

    def test_001_housekeeping_button(self):
        """ Testing the number of tasks assigned to the employee on the pms.housekeeping model.
        """
        self.hk_task = self.env['pms.housekeeping.task'].create({
            'name': 'clean room #1',
        })
        self.hk_task_1 = self.env['pms.housekeeping.task'].create({
            'name': 'clean room #2',
        })
        self.housekeeping = self.env['pms.housekeeping'].create({
            'task_id': self.hk_task.id,
            'employee_id': self.employee.id,
        })
        self.housekeeping = self.env['pms.housekeeping'].create({
            'task_id': self.hk_task.id,
            'employee_id': self.employee.id,
        })
        self.test_hk_employee = self.env['hr.employee'].search([('name', '=', 'Jon Doe')])
        count_empl = self.test_hk_employee.housekeeping_task
        self.assertEqual(count_empl, 2)
        housekeeper_id = self.env['pms.housekeeping'].search(
            self.test_hk_employee.activities_housekeeping()['domain']).employee_id.id
        employee_id = self.test_hk_employee.id
        self.assertEqual(housekeeper_id, employee_id)

    def test_002_maintenance_button(self):
        """ Testing the number of tasks assigned to the employee on the maintenance.request model.
        """
        self.mt_task = self.env['maintenance.request'].create({
            'name': 'calibrate #1',
            'user_id': self.user.id,
        })
        self.test_mt_employee = self.env['hr.employee'].search([('name', '=', 'Jon Doe')])
        count_empl = self.test_mt_employee.maintenance_task
        self.assertEqual(count_empl, 1)
        maintainer_id = self.env['maintenance.request'].search(
            self.test_mt_employee.activities_maintenance()['domain']).user_id.id
        employee_id = self.test_mt_employee.user_id.id
        self.assertEqual(maintainer_id, employee_id)

    def test_003_project_button(self):
        """ Testing the number of tasks assigned to the employee on the account.analytic.line model.
        """
        self.pt_account = self.env['account.analytic.account'].create({
            'name': 'account #1',
        })
        self.pt_task = self.env['account.analytic.line'].create({
            'name': 'task #1',
            'account_id': self.pt_account.id,
            'employee_id': self.employee.id,
        })
        self.test_pt_employee = self.env['hr.employee'].search([('name', '=', 'Jon Doe')])
        count_empl = self.test_pt_employee.project_task
        self.assertEqual(count_empl, 1)
        projector_id = self.env['account.analytic.line'].search(
            self.test_pt_employee.activities_project()['domain']).employee_id.id
        employee_id = self.test_pt_employee.id
        self.assertEqual(projector_id, employee_id)
