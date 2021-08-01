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
        'wizard/account_cash_book_wizard_view.xml',
        'report/account_cash_book_view.xml',
        'report/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
