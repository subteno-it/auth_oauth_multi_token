# -*- coding: utf-8 -*-
# Florent de Labarre - 2016

import time
import openerp
from collections import defaultdict
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _
from openerp.addons.auth_signup.res_users import SignupError

class auth_oauth_multi_token(models.Model):
    """Class defining the configuration values of an OAuth2 provider"""

    _name = 'auth.oauth.multi.token'
    _description = 'OAuth2 token'
    _order = "id desc"

    oauth_access_token = fields.Char('OAuth Access Token', readonly=True, copy=False)
    user_id = fields.Many2one('res.users', 'User', required=True)


class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_access_token_ids = fields.One2many('auth.oauth.multi.token', 'user_id', 'Work Centers', copy=True)

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        res = super(ResUsers, self)._auth_oauth_signin(provider, validation, params)
        try:
            oauth_uid = validation['user_id']
            user_ids = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)]).ids
            if user_ids:
                token_ids = self.env['auth.oauth.multi.token']
                token_ids.create({'user_id':user_ids[0],
                                    'oauth_access_token': params['access_token']})
        except:
            pass
        return res

    @api.model
    def check_credentials(self, password):
        try:
            return super(ResUsers, self).check_credentials(password)
        except openerp.exceptions.AccessDenied:
            res = self.env['auth.oauth.multi.token'].sudo().search([
                                ('user_id', '=', self.env.uid),
                                ('oauth_access_token', '=', password)],
                                                        )
            if not res:
                raise