# -*- coding: utf-8 -*-
# Florent de Labarre - 2016

import openerp
from openerp import api, fields, models, _
from openerp.addons.auth_signup.res_users import SignupError


class auth_oauth_multi_token(models.Model):
    """Class defining list of tokens"""

    _name = 'auth.oauth.multi.token'
    _description = 'OAuth2 token'
    _order = "id desc"

    oauth_access_token = fields.Char('OAuth Access Token', readonly=True, copy=False)
    user_id = fields.Many2one('res.users', 'User', required=True)
    active_token = fields.Boolean('Active')

    @api.model
    def create(self, vals):
        res = super(auth_oauth_multi_token, self).create(vals)
        oauth_access_token_ids = self.search([('user_id' ,'=', vals['user_id']), ('active_token', '=', True)], ).ids
        oauth_access_max_token = self.env['res.users'].search([('id', '=', vals['user_id'])], limit=1).oauth_access_max_token
        if len(oauth_access_token_ids) >= oauth_access_max_token:
            self.browse(oauth_access_token_ids[oauth_access_max_token]).write({
                            'oauth_access_token':"****************************",
                            'active_token': False})

        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_access_token_ids = fields.One2many('auth.oauth.multi.token', 'user_id', 'Tokens', copy=False)
    oauth_access_max_token = fields.Integer('Number of simultaneous connection', default=5, required=True)

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        res = super(ResUsers, self)._auth_oauth_signin(provider, validation, params)

        oauth_uid = validation['user_id']
        user_ids = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)]).ids
        if not user_ids:
            raise openerp.exceptions.AccessDenied()
        assert len(user_ids) == 1

        self.oauth_access_token_ids.create({'user_id': user_ids[0],
                                            'oauth_access_token': params['access_token'],
                                            'active_token': True,
                                            })
        return res

    @api.multi
    @api.depends('oauth_access_max_token')
    def clear_token(self):
        for users in self:
            for token in users.oauth_access_token_ids:
                token.write({
                                'oauth_access_token':"****************************",
                                'active_token': False})

    @api.model
    def check_credentials(self, password):
        try:
            return super(ResUsers, self).check_credentials(password)
        except openerp.exceptions.AccessDenied:
            res = self.env['auth.oauth.multi.token'].sudo().search([
                ('user_id', '=', self.env.uid),
                ('oauth_access_token', '=', password),
                ('active_token', '=', True),]
                ,
            )
            if not res:
                raise
