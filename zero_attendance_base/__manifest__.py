# -*- coding: utf-8 -*-
{
    'name': 'Zero Attendance Base',
    'version': '1.0',
    "summary": "base hr addon for Zero Systems HR",
    'description': """--((Must Install hr_holidays_public  from https://apps.odoo.com/apps/modules/12.0/hr_holidays_public/))
    before installing this addon---
    
    this addon is the base addon for Zero Systems Hr addons.
    
    tested on odoo community and enterprise-Support English and Arabic interface""",
    'depends': ['hr_attendance','zero_contract_work_hours'],
    'category': "Human Resources",
    'author': 'Zero Systems',
    'company': 'Zero for Information Systems',
    'website': "https://www.erpzero.com",
    'email': "sales@erpzero.com",
    'data': [
    ],
    'images': ['static/description/logo.PNG'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
