# -*- coding: utf-8 -*-

import time
from odoo import api, models, fields, _
from odoo.exceptions import UserError
ahs_flow_report

class CashFlow(models.Model):
    _inherit = 'account.account'

    def get_cash_flow_ids(self):
        cash_flow_id = self.env.ref('cahs_flow_report.account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_type = fields.Many2one('account.financial.report', string="Cash Flow type", domain=get_cash_flow_ids)

    @api.onchange('cash_flow_type')
    def onchange_cash_flow_type(self):
        for rec in self.cash_flow_type:
            # update new record
            rec.write({
                'account_ids': [(4, self._origin.id)]
            })

        if self._origin.cash_flow_type.ids:
            for rec in self._origin.cash_flow_type:
                # remove old record
                rec.write({'account_ids': [(3, self._origin.id)]})
