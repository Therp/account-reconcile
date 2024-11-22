# Copyright 2024 Therp BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from freezegun import freeze_time

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountReconcileNoNumericalToken(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company = cls.company_data["company"]

        cls.bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)], limit=1
        )

    @classmethod
    def _create_st_line(
        cls, amount=1000.0, date="2019-01-01", payment_ref="turlututu", **kwargs
    ):
        st_line = cls.env["account.bank.statement.line"].create(
            {
                "journal_id": kwargs.get("journal_id", cls.bank_journal.id),
                "amount": amount,
                "date": date,
                "payment_ref": payment_ref,
                "partner_id": cls.partner_a.id,
                **kwargs,
            }
        )
        return st_line

    @classmethod
    def _create_reconcile_model(cls, **kwargs):
        return cls.env["account.reconcile.model"].create(
            {
                "name": "test",
                "rule_type": "invoice_matching",
                "allow_payment_tolerance": True,
                "payment_tolerance_type": "percentage",
                "payment_tolerance_param": 0.0,
                **kwargs,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                            "amount_type": "percentage",
                            "label": f"test {i}",
                            **line_vals,
                        }
                    )
                    for i, line_vals in enumerate(kwargs.get("line_ids", []))
                ],
                "partner_mapping_line_ids": [
                    Command.create(line_vals)
                    for i, line_vals in enumerate(
                        kwargs.get("partner_mapping_line_ids", [])
                    )
                ],
            }
        )

    @freeze_time("2019-01-01")
    def test_invoice_matching_using_match_text_location(self):
        @contextmanager
        def rollback():
            savepoint = self.cr.savepoint()
            yield
            savepoint.rollback()

        rule = self._create_reconcile_model(
            match_partner=False,
            allow_payment_tolerance=False,
            match_text_location_label=False,
            match_text_location_reference=False,
            match_text_location_note=False,
        )
        st_line = self._create_st_line(amount=1000, partner_id=False)
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2019-01-01",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        term_line = invoice.line_ids.filtered(
            lambda x: x.display_type == "payment_term"
        )
        invoice2 = invoice.copy()
        invoice2.action_post()
        term_line2 = invoice2.line_ids.filtered(
            lambda x: x.display_type == "payment_term"
        )

        # No match at all.
        self.assertDictEqual(
            rule._apply_rules(st_line, None),
            {},
        )

        with rollback():
            # both will match because when chars are stripped they contain 1234
            term_line.name = "1a2b3c4d"
            term_line2.name = "x1y2z3z4"
            st_line.payment_ref = "1234"

            # matching when numerical tokens are enabled
            self.assertDictEqual(
                rule._apply_rules(st_line, None),
                {"amls": term_line + term_line2, "model": rule},
            )

            # not matching when numerical tokens are disabled
            rule.no_numerical_tokens = True
            term_line2.name = "1234"
            self.assertDictEqual(
                rule._apply_rules(st_line, None),
                {"amls": term_line2, "model": rule},
            )
