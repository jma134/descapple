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
    'name': 'HTC Master EDI Viewer',
    'version': '1.0',
    'author': 'Sam Ma',
    'summary': 'Transport & Distribute, Logistic',
    'description' : """
        designed for DSC HTC T&D Team
    """,
    'website': 'http://www.dhl.com',
    'images': ['images/htc.jpg'],
    'depends': ['product', 'account'],
    'category': 'Transport Platform',
    'sequence': 18,
    'data': [
        'security/htc_security.xml',
        'security/ir.model.access.csv',
        'views/htc_view.xml',
    ],
    'installable': True,
#    'application': True,
    'auto_install': False,
#    'css': [ 'static/src/css/htc.css' ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
