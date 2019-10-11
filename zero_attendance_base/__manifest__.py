# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 - now Bytebrand Outsourcing AG (<http://www.bytebrand.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Zero Attendance Base',
    'version': '12.1.0',
    "summary": "base hr addon for Zero Systems HR",
    'description': """--((Must Install hr_holidays_public  from https://apps.odoo.com/apps/modules/12.0/hr_holidays_public/))
    before installing this addon---
    
    this addon is the base addon for Zero Systems Hr addons. 
    the system counts the missing/un-attended workday hours that the employee took in a workday he/she actually was present on,
        but he/she took no permission/leave for those hours
    
    tested on odoo community and enterprise-Support English and Arabic interface""",
    'depends': ['hr_attendance','zero_contract_work_hours',
        'hr_holidays_public'],
    'author': 'Zero Systems',
    'company': 'Zero for Information Systems',
    'website': "https://www.erpzero.com",
    'email': "sales@erpzero.com",
    'category': "Human Resources",
    'data': [
    ],
    'images': ['static/description/logo.PNG'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
