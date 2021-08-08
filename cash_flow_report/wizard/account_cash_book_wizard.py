# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashBookWizard(models.TransientModel):

    _name = 'account.cash.book.wizard'
    _description = 'Account Cash Book Report'

    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 default=lambda self: self.env.user.company_id,)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')
    date_from = fields.Date(string='Start Date', default=date.today()-timedelta(days=7),
                            requred=True)
    date_to = fields.Date(string='End Date', default=date.today(),
                          requred=True)
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by',
        required=True, default='sort_date')
    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.',
                                     default=True)
    account_id = fields.Many2one('account.account',
                                   'Account',)
    journal_id = fields.Many2one('account.journal',
                                   string='Journal', required=True,)

    @api.onchange("journal_id")
    def onchnage_journal_id(self):
        if self.journal_id:
            self.account_id = self.journal_id.default_credit_account_id


    def _build_contexts(self, data):
        result = {}
        result['journal_id'] = 'journal_id' in data['form'] and data['form'][
            'journal_id'] or False
        result['state'] = 'target_move' in data['form'] and data['form'][
            'target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def check_report(self):
        self.ensure_one()
        if self.initial_balance and not self.date_from:
            raise UserError(_("You must choose a Start Date"))
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_id', 'target_move',
             'display_account',
             'account_id', 'sortby', 'initial_balance'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(
            self, 'cash_flow_report.report_cash_book', data=data)
