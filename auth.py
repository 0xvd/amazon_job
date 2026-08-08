import base64
import json
import time

from network import AmazonRequest, BaseRequest


class AmazonAuth(AmazonRequest):    
    def __init__(self, req: BaseRequest, region='IN'):
        super().__init__(req, region)

    def call_auth_api(self, path, payload=None, params=None, headers=None, **kwargs):
        payload = {
            'token': self.csrf,
            **(payload or {})
        } if self.csrf else payload

        return super().call_auth_api(path, payload, params, headers, **kwargs)

    def _verify_email(self, email):
        for _ in range(6):
            self.rum_event()

        self.update_cwr_s('LOGIN')

        for _ in range(2):
            self.rum_event(interaction=True)

        for _ in range(3):
            self.rum_event()

        data = self.call_auth_api(
            'candidate/v2',
            payload={
                'allowedConflictedBBRegion': self.conflict_region,
                'candidateLoginProp': email,
                'countryName': self.countryName,
                'token': self.csrf,
            },
        )

        if not data.get('isActive'):
            return {
                'status': False,
                'message': 'User is not Active',
            }
        if data.get('isEmailVerified') or data.get('isPhoneVerified'):
            return {
                'status': True,
                'LoginMethod': data.get('loginMethod'),
            }

        for _ in range(2):
            self.rum_event(interaction=True)    
        return {
            'status': False,
            'messgae': 'Unexcepted Error occured'
        }

    def _login(self, email: str, pin: int):
        verify_email_data = self._verify_email(email)
        if not verify_email_data.get('status'):
            return verify_email_data

        for _ in range(4):
                self.rum_event()

        self.update_cwr_s('PIN', 'LOGIN')

        for _ in range(3):
            self.rum_event(interaction=True)

        for _ in range(3):
            self.rum_event()

        logged_in = self.call_auth_api('authentication/verify-sign-in', payload={
            'user': email,
            'pin': pin,
        })

        if not logged_in.get('verificationPassed'):
            return {
                'status': False,
                'message': logged_in['errorMessage']
            }

        return {
            'status': True,
            'data': logged_in
        }

    def rum_event(self, interaction=False):
        self.cwr_event_count += 1
        if interaction:
            self.cwr_interaction += 1

    def send_otp(self, email, pin, loginType):
        for _ in range(4):
            self.rum_event()

        self.rum_event(interaction=True)

        payload = {
            'locale': 'en-IN',
            'loginType': loginType,
            'user': email,
            'pin': pin,
        }
        data = self.call_auth_api('authentication/sign-in', payload=payload)
        _session = data.get('session')
        if not _session:
            return {
                'status': False,
                'message': 'Unable to send otp'
            }
        return {
            'status': True,
            'data': {
                'session': _session
            }
        }

    def _perform_2FA(self, otp, email, session):
        payload = {
            'user': email,
            'session': session,
            'otp': otp,
        }
        data = self.call_auth_api('authentication/confirm-otp', payload=payload)
        message = data.get('message') or data.get('errorMessage') or ''
        if 'a valid verification' in message:
            return {
                'status': False,
                'message': message
            }
        elif 'code in not valid' in message:
            return {
                'status': False,
                'message': message
            }
        
        return {
            'status': True,
            'data': data
        }

if __name__ == '__main__':
    amazon_auth = AmazonAuth(BaseRequest())
    email = 'iamhelooworld@gmail.com'
    pin = '000123'
    etype = 'email'
    amazon_auth._login(email=email, pin=pin)
    otp_data = amazon_auth.send_otp(email, pin, etype)
    session = otp_data.get('data').get('session')
    otp = input('Enter OTP: ')
    data = amazon_auth._perform_2FA(otp, email, session)
    print(data)
