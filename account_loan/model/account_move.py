# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_line_id = fields.Many2one(
        'account.loan.line',
        readonly=True,
        ondelete='restrict',
    )
    loan_id = fields.Many2one(
        'account.loan',
        readonly=True,
        store=True,
        ondelete='restrict',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('loan_line_id'):
                loan_line_id = self.env['account.loan.line'].browse(vals.get('loan_line_id'))
                if (loan_line_id and loan_line_id.long_term_loan_account_id
                        and loan_line_id.long_term_principal_amount != 0):
                    line_ids = vals.get('line_ids', [])
                    line_ids.append((0, 0, {
                        'account_id':
                        loan_line_id.loan_id.short_term_loan_account_id.id,
                        'credit':
                        loan_line_id.long_term_principal_amount,
                        'debit':
                        0,
                    }))
                    line_ids.append((0, 0, {
                        'account_id': loan_line_id.long_term_loan_account_id.id,
                        'credit': 0,
                        'debit': loan_line_id.long_term_principal_amount,
                    }))
                    vals['line_ids'] = line_ids
        return super().create(vals_list)

    def post(self):
        res = super().post()
        for record in self:
            loan_line_id = record.loan_line_id
            if record.loan_line_id:
                record.loan_id = loan_line_id.loan_id
                record.loan_line_id.check_move_amount()
                record.loan_line_id.loan_id.compute_posted_lines()
                if record.loan_line_id.sequence == record.loan_id.periods:
                    record.loan_id.close()
        return res
