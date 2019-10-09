{
    'name':'Zero Attendance Base',
    'version':'12.0.1',
    'author':'Zero Systems',
    'company':'Zero for Information Systems',
    'website':'https://www.erpzero.com',
    'email': 'sales@erpzero.com',
    'category':'Human Resources',
    "description": """this addon is the base addon for Zero Systems Hr addons""",
    'depends': [
        'hr',
        'hr_holidays_public',
        'hr_attendance',
        'zero_contract_work_hours',
    ],
    "demo": [
    ],
    "data": [
    ],
    'images': ['static/description/logo.PNG'],
    "installable": True,
    "auto_install": False,
    "application": True,
}
