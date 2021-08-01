# -*- coding: utf-8 -*-
from datetime import date

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
    date_from = fields.Date(string='Start Date', default=date.today(),
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

    def _get_default_account_ids(self):
        journals = self.env['account.journal'].search([('type', '=', 'cash')])
        accounts = []
        for journal in journals:
            accounts.append(journal.default_credit_account_id.id)
        return accounts

    account_ids = fields.Many2many('account.account',
                                   'account_report_cashbook_account_rel',
                                   'report_id', 'account_id',
                                   'Accounts',
                                   default=_get_default_account_ids)
    journal_ids = fields.Many2many('account.journal',
                                   'account_report_cashbook_journal_rel',
                                   'account_id', 'journal_id',
                                   string='Journals', required=True,
                                   default=lambda self: self.env[
                                       'account.journal'].search([("type", "=", "cash")]))

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form'][
            'journal_ids'] or False
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
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'display_account',
             'account_ids', 'sortby', 'initial_balance'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                            lang=self.env.context.get(
                                                'lang') or 'en_US')
        return self._print_report(data)

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(
            self, 'cash_flow_report.report_cash_book', data=data)
