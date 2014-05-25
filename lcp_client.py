from pylcp.api import Client
import json


class LCPClient(Client):

    def __init__(self, app):
        super(LCPClient, self).__init__(
            app.config['LCP_URL'],
            app.config['LCP_MAC_KEY_IDENTIFIER'],
            app.config['LCP_MAC_KEY_SECRET'])
        self.mv_url = app.config['LCP_MV_URL']
        self.credit_url = app.config['LCP_CREDIT_URL']
        self.credit_amount = app.config['LCP_CREDIT_AMOUNT']

    def validate_member(self, user):
        lcp_response = self.post(
            self.mv_url, data=self._create_mv_data(user))
        lcp_response.raise_for_status()
        return lcp_response.json()


    def do_credit(self, user):
        lcp_response = self.post(
            self.credit_url, data=self._create_credit_data(user))
        lcp_response.raise_for_status()
        return lcp_response.json()


    def _create_mv_data(self, user):
        return json.dumps({
            'firstName': user.first_name,
            'lastName': user.last_name,
            'memberId': user.membership_number
        })

    def _create_credit_data(self, user):
        return json.dumps({
            'amount': self.credit_amount,
            'memberValidation': user.mv_url,
            # 'firstName': user.first_name,
            # 'lastName': user.last_name,
            # 'email': user.email
        })
