# Copyright 2024 Therp BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    no_numerical_tokens = fields.Boolean(
        "No numerical token matching", help="Don't match on numerical tokens"
    )

    def _get_invoice_matching_st_line_tokens(self, st_line):
        (
            numerical_tokens,
            exact_tokens,
            _text_tokens,
        ) = super()._get_invoice_matching_st_line_tokens(st_line)
        if self.no_numerical_tokens:
            return [], exact_tokens, _text_tokens
        return numerical_tokens, exact_tokens, _text_tokens
