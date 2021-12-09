from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super()._create_payments()
        invoices = payments.reconciled_invoice_ids.filtered('invoice_line_ids.folio_line_ids')
        for invoice in invoices:
            invoice_payments = invoice._get_reconciled_payments().filtered(lambda pay: pay in payments)
            payment_tuples = [(4, payment.id, 0) for payment in invoice_payments]
            folios = invoice.invoice_line_ids.folio_line_ids.folio_id
            folio_tuples = [(4, folio.id, 0) for folio in folios]
            folios.write({'payment_ids': payment_tuples})
            invoice_payments.move_id.line_ids.write({'folio_ids': folio_tuples})
            folios._compute_amount()
        return payments
