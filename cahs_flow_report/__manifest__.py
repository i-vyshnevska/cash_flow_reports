# -*- coding: utf-8 -*-

{
    'name': 'Cash flow report',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'summary': """Day-Bank-Cash book reports""",
    'description': """Cash flow odoo report 10
                    """,
    'author': '',
    'maintainer': 'OCA',
    'depends': [
        'account', 
        'sale', 
        ],
    'data': [
        'data/cash_flow_data.xml',
        'views/accounting_menu.xml',
    #     'views/res_config_view.xml',
        'wizard/cash_flow_report.xml',
        'wizard/account_cash_book_wizard_view.xml',
    #     'wizard/account_day_book_wizard_view.xml',
    #     'report/report_financial.xml',
        'report/cash_flow_report.xml',
    #     'report/account_bank_book_view.xml',
        'report/account_cash_book_view.xml',
    #     'report/account_day_book_view.xml',
        'report/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
