# -*- coding: utf-8 -*-

from openerp import models, fields, api

class transport_prealert(models.TransientModel):
    _name = 'transport.prealert'

#     def _default_sessions(self):
#         return self.env['transport.session'].browse(self._context.get('active_ids'))

    period_from = fields.Datetime('Start period')
    period_to = fields.Datetime('End period')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves')

    def transport_prealert_open_window(self, cr, uid, ids, context=None):
        print "Pre-Alert"
        data = self.read(cr, uid, ids, context=context)
        print data #[{'create_uid': (1, u'Administrator'), 'create_date': '2015-04-17 07:30:31', '__last_update': '2015-04-17 07:30:31', 'period_to': '2015-04-22 07:29:37', 'write_uid': (1, u'Administrator'), 'period_from': '2015-04-17 07:29:32', 'write_date': '2015-04-17 07:30:31', 'display_name': u'transport.prealert,4', 'id': 4, 'target_move': u'posted'}]
        print data[0] #get the first record {'x': 'AF', 'asdf', 332}
        
        
class transport_wizardtest(models.TransientModel):
    _name = 'transport.wizardtest'


    period_from = fields.Datetime('Start period')
    period_to = fields.Datetime('End period')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves')

    def transport_wizardtest_open_window(self, cr, uid, ids, context=None):
        print "Pre-Alert"
        data = self.read(cr, uid, ids, context=context)
        print data #[{'create_uid': (1, u'Administrator'), 'create_date': '2015-04-17 07:30:31', '__last_update': '2015-04-17 07:30:31', 'period_to': '2015-04-22 07:29:37', 'write_uid': (1, u'Administrator'), 'period_from': '2015-04-17 07:29:32', 'write_date': '2015-04-17 07:30:31', 'display_name': u'transport.prealert,4', 'id': 4, 'target_move': u'posted'}]
        print data[0] #get the first record {'x': 'AF', 'asdf', 332}
        return {}        