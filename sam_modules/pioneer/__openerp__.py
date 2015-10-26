# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Pioneer SDD Platform',
    'version': '1.0',
    'author': 'Sam Ma',
    'summary': 'Inner City Distribute',
    'description' : """
        designed for DSC Apple T&D Team
    """,
    'website': 'http://www.dhl.com',
    'images': ['images/pioneer.jpg'],
    'depends': ['product', 'account'],
    'category': 'Transport Platform',
    'sequence': 1,
    'data': [
#         'security/security.xml',
#         'security/ir.model.access.csv',
        #'wizard/vmi_location_product_view.xml',
        'views/pioneer_view.xml',
        'views/pioneer_order_maps.xml',
#         'views/pioneer_workflow.xml',
#         'views/partner.xml',             
#         'views/pioneer_eml_data.xml',

    ],
    'installable': True,
#    'application': True,
    'auto_install': False,
#    'css': [ 'static/src/css/vmi.css' ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
