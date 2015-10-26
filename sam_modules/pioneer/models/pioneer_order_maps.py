# -*- coding: utf-8 -*-
##############################################################################
#
#    Partner External Maps module for Odoo
#    Copyright (C) 2015 Akretion (http://www.akretion.com/)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging

from openerp.addons.base_geoengine import geo_model, fields as FD

logger = logging.getLogger(__name__)


class PioneerOrder(models.Model):
    _inherit = 'pioneer.order'
    
#     geo_point = FD.GeoPoint('Addresses coordinate', readonly=True)

    @api.model
    def _address_as_string(self):
        addr = []
        if self.street:
            addr.append(self.street)
        if self.street2:
            addr.append(self.street2)
        if self.city:
            addr.append(self.city)
        if self.state_id:
            addr.append(self.state_id.name)
#         if self.country_id:
#             addr.append(self.country_id.name)
        addr.append('China')
        if not addr:
            raise Warning(
                _("Address missing on Order: '%s'.") % self.name)
        address = ' '.join(addr)
        return address

    @api.model
    def _prepare_url(self, url, replace):
        assert url, 'Missing URL'
        for key, value in replace.iteritems():
            if not isinstance(value, (str, unicode)):
                # for latitude and longitude which are floats
                value = unicode(value)
            url = url.replace(key, value)
        logger.debug('Final URL: %s', url)
        return url

    @api.multi
    def open_map(self):
        if not self.env.user.context_map_website_id:
            raise Warning(
                _('Missing map provider: '
                  'you should set it in your preferences.'))
        map_website = self.env.user.context_map_website_id
        if (
                map_website.lat_lon_url and
                hasattr(self, 'partner_latitude') and
                self.partner_latitude and self.partner_longitude):
            url = self._prepare_url(
                map_website.lat_lon_url, {
                    '{LATITUDE}': self.partner_latitude,
                    '{LONGITUDE}': self.partner_longitude})
        else:
            if not map_website.address_url:
                raise Warning(
                    _("Missing parameter 'URL that uses the address' "
                      "for map website '%s'.") % map_website.name)
            url = self._prepare_url(
                map_website.address_url,
                {'{ADDRESS}': self._address_as_string()})
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
            }

    @api.multi
    def open_route_map(self):
        if not self.env.user.context_route_map_website_id:
            raise Warning(
                _('Missing route map website: '
                  'you should set it in your preferences.'))
        map_website = self.env.user.context_route_map_website_id
        if not self.env.user.context_route_start_partner_id:
            raise Warning(
                _('Missing start address for route map: '
                  'you should set it in your preferences.'))
        start_partner = self.env.user.context_route_start_partner_id
        if (
                map_website.route_lat_lon_url and
                hasattr(self, 'partner_latitude') and
                self.partner_latitude and
                self.partner_longitude and
                start_partner.partner_latitude and
                start_partner.partner_longitude):
            url = self._prepare_url(
                map_website.route_lat_lon_url, {
                    '{START_LATITUDE}': start_partner.partner_latitude,
                    '{START_LONGITUDE}': start_partner.partner_longitude,
                    '{DEST_LATITUDE}': self.partner_latitude,
                    '{DEST_LONGITUDE}': self.partner_longitude})
        else:
            if not map_website.route_address_url:
                raise Warning(
                    _("Missing route URL that uses the addresses "
                        "for the map website '%s'") % map_website.name)
            url = self._prepare_url(
                map_website.route_address_url, {
                    '{START_ADDRESS}': start_partner._address_as_string(),
                    '{DEST_ADDRESS}': self._address_as_string()})
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
            }
