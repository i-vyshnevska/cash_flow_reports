# -*- coding: utf-8 -*-
import time
from datetime import timedelta, datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ReportCashBook(models.AbstractModel):
    _name = 'report.cash_flow_report.report_cash_book'
    _description = 'Cash Book Report'


    def _get_account_move_entry(self, account_id, init_balance, form_data, pass_date):
        cr = self.env.cr
        move_line = self.env['account.move.line']
        move_lines = []
        res = {}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = move_line.with_context(
                date_from=self.env.context.get('date_from'), date_to=False,
                initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id',
                                           'm').replace('account_move_line',
                                                        'l')
            sql = ("""SELECT 0 AS lid, 
                        l.account_id AS account_id, 
                        '' AS ldate, 
                        '' AS lcode, 
                        0.0 AS amount_currency, 
                        '' AS lref, 
                        'Initial Balance' AS lname, 
                        COALESCE(SUM(l.debit),0.0) AS debit, 
                        COALESCE(SUM(l.credit),0.0) AS credit, 
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, 
                        '' AS lpartner_id,\
                    '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                    NULL AS currency_id,\
                    '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                    '' AS partner_name\
                    FROM account_move_line l\
                    LEFT JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    WHERE l.account_id = %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple([account_id]) + tuple(init_where_params))
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines.append(row)


        tables, where_clause, where_params = move_line._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        if form_data['target_move'] == 'posted':
            target_move = "AND m.state = 'posted'"
        else:
            target_move = ''
        sql = ('''
                SELECT l.id AS lid, acc.name as accname, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, 
                l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, 
                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
                m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                JOIN account_account acc ON (l.account_id = acc.id) 
                WHERE l.account_id = %s AND l.journal_id = %s ''' + target_move + ''' AND l.date = %s
                GROUP BY l.id, l.account_id, l.date,
                     j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name , acc.name
                     ORDER BY l.date DESC
        ''')
        params = tuple([account_id, form_data['journal_id'][0], pass_date])
        cr.execute(sql, params)
        data = cr.dictfetchall()
        
        debit = credit = balance = 0.00
        for line in data:
            debit += line['debit']
            credit += line['credit']
            balance += line['balance']
        res['debit'] = debit
        res['credit'] = credit
        res['balance'] = balance
        for ml in move_lines:
            res['balance'] += ml['balance']
        res["end_balance"] = balance
        res['lines'] = data
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
    
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        form_data = data['form']
        codes = []
        # if data['form'].get('journal_id', False):
        code = self.env['account.journal'].browse(data['form'].get('journal_id')[0]).code
        account = data['form'].get('account_id')[0]

        date_start = datetime.strptime(form_data['date_from'], '%Y-%m-%d').date()
        date_end = datetime.strptime(form_data['date_to'], '%Y-%m-%d').date()
        days = date_end - date_start
        init_balance = form_data['initial_balance']
        dates = []
        record = []
        for i in range(days.days + 1):
            dates.append(date_start + timedelta(days=i))
        for head in dates:
            pass_date = str(head)
            accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(account, init_balance, form_data, pass_date)
            if accounts_res['lines']:
                record.append({
                    'date': head,
                    'end_balance': accounts_res['end_balance'],
                    'debit': accounts_res['debit'],
                    'credit': accounts_res['credit'],
                    'balance': accounts_res['balance'],
                    'child_lines': accounts_res['lines']
                })
            
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'start_balance': self._get_start_balance(account, init_balance, form_data, pass_date),
            'docs': docs,
            'time': time,
            'Accounts': record,
            'print_journal': codes,
        }

    def render_html(self, docids, data=None):
        docargs = self._get_report_values(docids, data=data)
        return self.env['report'].render("cash_flow_report.report_cash_book", docargs)

    def _get_start_balance(self, account_id, init_balance, form_data, pass_date):
        # start balance
        move_line = self.env['account.move.line']
        cr = self.env.cr
        yesterday = fields.Date.to_string(fields.Datetime.from_string(form_data["date_from"]) - timedelta(days=1))
        init_tables, init_where_clause, init_where_params = move_line.with_context(
            date_from=False, date_to=yesterday,
            initial_bal=False)._query_get()
        init_wheres = [""]
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id',
                                        'm').replace('account_move_line',
                                                    'l')
        sql = ("""SELECT 0 AS lid, 
                    l.account_id AS account_id, 
                    '' AS ldate, 
                    '' AS lcode, 
                    0.0 AS amount_currency, 
                    '' AS lref, 
                    'Initial Balance' AS lname, 
                    COALESCE(SUM(l.debit),0.0) AS debit, 
                    COALESCE(SUM(l.credit),0.0) AS credit, 
                    COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, 
                    '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id = %s""" + filters + ' GROUP BY l.account_id')
        params = (tuple([account_id]) + tuple(init_where_params))
        cr.execute(sql, params)
        result = cr.dictfetchall()
        if result:
            return result[0]["balance"]
        return 0