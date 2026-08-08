import typing
import json
import base64
import uuid
import random
import time
import pathlib

from curl_cffi import requests, CurlMime, CurlOpt
from curl_cffi.requests.exceptions import ProxyError
from awf_challenge import AwfSolver

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'

_DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    'sec-ch-ua': 'Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151',
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.6",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}

_DEFAULT_COOKIES = {
    'hvh-locale': 'en-US',
    'cwr_u': str(uuid.uuid4()),
    'hvh-locale': 'en-IN',
    'at_check': 'true',
}

REGIONS = {
  "US": {
    "countryCode": "US",
    "countryName": "United States",
    "allowedConflictedBBRegion": "US"
  },
  "MX": {
    "countryCode": "MX",
    "countryName": "Mexico",
    "allowedConflictedBBRegion": "MX"
  },
  "UK": {
    "countryCode": "UK",
    "countryName": "United Kingdom",
    "allowedConflictedBBRegion": "UK"
  },
  "CA": {
    "countryCode": "CA",
    "countryName": "Canada",
    "allowedConflictedBBRegion": "CA"
  },
  "IN": {
    "countryCode": "IN-CS",
    "countryName": "India-CS",
    "allowedConflictedBBRegion": "IN"
  },
  "IE": {
    "countryCode": "IE",
    "countryName": "Ireland",
    "allowedConflictedBBRegion": "IE"
  },
  "JP": {
    "countryCode": "JP",
    "countryName": "Japan",
    "allowedConflictedBBRegion": "JP"
  },
  "PH": {
    "countryCode": "PH",
    "countryName": "Philippines",
    "allowedConflictedBBRegion": "PH"
  },
  "ZA": {
    "countryCode": "ZA",
    "countryName": "South Africa",
    "allowedConflictedBBRegion": "ZA"
  },
  "BR": {
    "countryCode": "BR",
    "countryName": "Brazil",
    "allowedConflictedBBRegion": "BR"
  },
  "CO": {
    "countryCode": "CO",
    "countryName": "Colombia",
    "allowedConflictedBBRegion": "CO"
  },
  "CR": {
    "countryCode": "CR",
    "countryName": "Costa Rica",
    "allowedConflictedBBRegion": "CR"
  },
  "AE": {
    "countryCode": "AE",
    "countryName": "United Arab Emirates",
    "allowedConflictedBBRegion": "AE"
  },
  "EG": {
    "countryCode": "EG-CS",
    "countryName": "Egypt-CS",
    "allowedConflictedBBRegion": "EG"
  },
  "JO": {
    "countryCode": "JO",
    "countryName": "Jordan",
    "allowedConflictedBBRegion": "JO"
  },
  "SA": {
    "countryCode": "SA",
    "countryName": "Kingdom of Saudi Arabia",
    "allowedConflictedBBRegion": "SA"
  },
  "DE": {
    "countryCode": "DE",
    "countryName": "Germany",
    "allowedConflictedBBRegion": "DE"
  },
  "AU": {
    "countryCode": "AU",
    "countryName": "Australia",
    "allowedConflictedBBRegion": "AU"
  },
  "CZ": {
    "countryCode": "CZ",
    "countryName": "Czech Republic",
    "allowedConflictedBBRegion": "CZ"
  },
  "ES": {
    "countryCode": "ES",
    "countryName": "Spain",
    "allowedConflictedBBRegion": "ES"
  },
  "FR": {
    "countryCode": "FR",
    "countryName": "France",
    "allowedConflictedBBRegion": "FR"
  },
  "IT": {
    "countryCode": "IT",
    "countryName": "Italy",
    "allowedConflictedBBRegion": "IT"
  },
  "MA": {
    "countryCode": "MA",
    "countryName": "Morocco",
    "allowedConflictedBBRegion": "MA"
  },
  "NL": {
    "countryCode": "NL",
    "countryName": "Netherlands",
    "allowedConflictedBBRegion": "NL"
  },
  "PL": {
    "countryCode": "PL",
    "countryName": "Poland",
    "allowedConflictedBBRegion": "PL"
  },
  "PT": {
    "countryCode": "PT",
    "countryName": "Portugal",
    "allowedConflictedBBRegion": "PT"
  },
  "RO": {
    "countryCode": "RO",
    "countryName": "Romania",
    "allowedConflictedBBRegion": "RO"
  },
  "SG": {
    "countryCode": "SG",
    "countryName": "Singapore",
    "allowedConflictedBBRegion": "SG"
  },
  "TR": {
    "countryCode": "TR",
    "countryName": "Turkey",
    "allowedConflictedBBRegion": "TR"
  }
}

class BaseRequest:
    def __init__(self, session=None) -> None:
        if session is not None:
            self.session = session
        else:
            self.session = self._create_request_session()
        self.session.curl.setopt(CurlOpt.HTTP_VERSION, 3)

    def _create_request_session(self):
        session = requests.Session()
        session.headers.update(_DEFAULT_HEADERS)
        session.cookies.update(_DEFAULT_COOKIES)
        return session

    def request(
        self,
        *,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        data: bytes | dict | None = None,
        timeout: float = 20,
        allow_status_codes: int | tuple  = None,
        **kwargs,
    ):
        headers = headers or {}
        headers = {str(k): str(v) for k, v in headers.items()}

        params = params or {}

        allow_status_codes = allow_status_codes
        if allow_status_codes is not None and not isinstance(
            allow_status_codes, typing.Iterable
        ):
            allow_status_codes = (allow_status_codes,)

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            **kwargs,
        )

        self.session.cookies.update(response.cookies)

        return response

    @staticmethod
    def files_to_mime(files: dict):
        mime = CurlMime()

        for name, data in files.items():
            if isinstance(data, (dict, list)):
                data = json.dumps(data, separators=(",", ":"))

            elif not isinstance(data, (str, bytes)):
                data = str(data)

            mime.addpart(
                name=name,
                data=data,
            )

        return mime

    def start_verbose(self):
        # def debug_callback(debug_type, data):
        #     print(data.decode("utf-8", errors="ignore"))
        self.session.curl.setopt(CurlOpt.VERBOSE, 1)
        # self.session.curl.setopt(CurlOpt.DEBUGFUNCTION, debug_callback)

class WebShare(BaseRequest):
    LIMIT = 1_000_000

    def __init__(self, req: BaseRequest, logger):
        super().__init__(session=req.session)
        self.key = None
        self.file = pathlib.Path("WEB_SHARE_KEYS.txt")
        self.active_keys = []
        self.deactive_keys = []
        self.proxies = []
        self._rotation_count = 0
        self._load_all_keys()
        self.get_key()
        self._load_all_proxies()
        self.logger = logger

    def get_key(self):
        if not self.active_keys:
            raise RuntimeError("No active API keys left")
        self.key = self.active_keys[0]
        return self.key

    def get_proxy(self):
        return self.proxies[0]

    def rotate(self):
        if not self.proxies:
            raise RuntimeError("No proxies available")

        self.proxies.append(self.proxies.pop(0))
        self._rotation_count += 1

        if self._rotation_count == len(self.proxies):
            self._rotation_count = 0
            self._rotate_api()

    def _rotate_api(self):
        if len(self.active_keys) > 1:
            self.active_keys.append(self.active_keys.pop(0))

        self.proxies.clear()
        self.get_key()
        self._load_all_proxies()
        
    def _load_all_keys(self):
        active = []
        deactive = []
        section = None

        for line in self.file.read_text().splitlines():
            if not(line := line.strip()):
                continue

            if line in ("#ACTIVE", "#DEACTIVE"):
                section = line[1:].lower()
                continue

            if section == "active":
                key, usage = line.split('|')
                active.append({
                    'key': str(key).strip(),
                    'usage': int(usage)
                })
            elif section == "deactive":
                key, usage, message = line.split('|')
                deactive.append({
                    'key': key.strip(),
                    'usage': int(usage),
                    'message': message.strip()
                })

        self.active_keys = active
        self.deactive_keys = deactive

    def _save_all_keys(self):
        keys_data = "#ACTIVE\n"

        new_active = []

        for key in self.active_keys:
            usage = key["usage"]

            if usage >= 100:
                self.deactive_keys.append(key)
            else:
                new_active.append(key)
                keys_data += f'{key["key"]} | {usage}\n'

        self.active_keys = new_active

        keys_data += "\n#DEACTIVE\n"

        for key in self.deactive_keys:
            usage = key["usage"]
            message = "Exceed API LIMIT" if usage >= 100 else "Unknown API Issue"
            keys_data += f'{key["key"]} | {usage} | {message}\n'

        self.file.write_text(keys_data)

    def refresh(self):
        if self._check_quota()["bandwidth_total"] >= self.LIMIT:
            self._deactivate_current()
            self._save_all_keys()
            self._load_all_keys()

        self.proxies.clear()
        self.get_key()
        self._load_all_proxies()

    def _deactivate_current(self, message="Exceed API LIMIT"):
        self.key["message"] = message
        self.key["usage"] = 100

    def _call_api(self, *, path, headers=None, **kwargs):  
        headers = {'Authorization': f'Token {self.key['key']}', **(headers or {})}
        return super().request(url=f'https://proxy.webshare.io/api/v2/{path}', headers=headers, **kwargs).json()

    def _load_all_proxies(self):
        data = self._call_api(path="proxy/list/", params={"mode": "direct"})
        for proxy in data.get('results') or []:
            if not proxy.get('valid'):
                continue
            username = proxy.get('username')
            password = proxy.get('password')
            if not (username and password):
                continue
            proxy = f'{username}:{password}@{proxy.get('proxy_address')}:{proxy.get('port')}'
            self.proxies.append(proxy)

    def _check_quota(self):
        return self._call_api(path='stats/aggregate')

    def request(
        self,
        *,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        data: bytes | dict | None = None,
        timeout: float = 20,
        allow_status_codes: int | tuple  = None,
        **kwargs,
    ):      
        proxy = self.get_proxy()
        self.logger.info(f'Using proxy {proxy}')
        _request = {
            'url': url, 
            'method': method, 
            'headers': headers, 
            'params': params, 
            'data': data, 
            'timeout': timeout, 
            'allow_status_codes': allow_status_codes,
            'proxy': proxy,
            **kwargs
        }
        try:
            return super().request(**_request)
        except ProxyError:
            self.logger.warn('Got Proxy error roatating proxy')
            self.rotate()
            return self.request(**_request)


class AmazonRequest(WebShare):
    def __init__(self, req: BaseRequest, logger, region='UK'):
        self.api_base = "https://auth.hiring.amazon.com/api"
        self.region_detail = REGIONS.get(region) or REGIONS['UK']
        self.region = self.region_detail['countryCode']
        self.conflict_region = self.region_detail['allowedConflictedBBRegion']
        self.countryName = self.region_detail['countryName']
        self.cwr_session_id = str(uuid.uuid4())
        self.cwr_event_count = 1
        self.cwr_interaction = 0
        self.waf_token = None
        self.csrf = None
        super().__init__(req)

        self.logger = logger()

    def aws_waf(self):
        if self.waf_token:
            token, waf_time = self.waf_token.split('#')
            if int(time.time()) - int(waf_time) <= 150:
                self.session.headers.update({'aws-waf-token': token})
                return
        new_token = AwfSolver()()
        self.waf_token = f'{new_token}#{int(time.time())}'
        self.session.headers.update({'aws-waf-token': new_token})

    def _get_csrf(self):
        if self.csrf and not self.is_jwt_expired(self.csrf):
            return
        csrf_resp = super().request(url=f'{self.api_base}/csrf', params={'countryCode': self.region}).json()
        csrf = csrf_resp.get('token')
        if not csrf:
            raise RuntimeError('No csrf found')
        self.csrf = csrf
        self.session.headers.update({'Csrf-Token': self.csrf})
        return

    @staticmethod
    def is_jwt_expired(jwt_token):
        if not (
            jwt_token and len(jwt_token.split('.')) == 3
        ):
            return False
        _, payload, _ = jwt_token.split('.') 
        payload = f'{payload}==' if not payload.endswith('==') else payload
        return json.loads(base64.b64decode(payload.encode()))['exp'] - time.time() < 300

    def request(
        self,
        *,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        data: bytes | dict | None = None,
        timeout: float = 20,
        allow_status_codes: int | tuple  = None,
        **kwargs,
    ):        
        self.aws_waf()
        self._get_csrf()
        return super().request(
            url=url,
            method=method,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            allow_status_codes=allow_status_codes,
            **kwargs
        )

    def call_auth_api(self, path, payload=None, params=None, headers=None, **kwargs):
        method = 'GET'
        if payload:
            method = 'POST'
            payload = {'countryName': self.countryName, **(payload or {})}

        return self.request(
            url=f'{self.api_base}/{path}',
            method=method,
            params={
                'countryCode': self.region,
                **(params or {})
            },
            json=payload,
            headers={   
                **({'x-hvh-auth-region-overwrite': 'UK'} if self.region_detail['allowedConflictedBBRegion'] == 'IN' else {}),
                'Origin': 'https://auth.hiring.amazon.com',
                'Referer': 'https://auth.hiring.amazon.com/',
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-GB,en;q=0.6",
                "Content-Type": "application/json",
                "Origin": "https://auth.hiring.amazon.com",
                "Referer": "https://auth.hiring.amazon.com/",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                **(headers or {})
            },
            **kwargs
        ).json()

    def update_cwr_s(self, page_id, parent_page=None):
        self.cwr_event_count += random.randint(8, 20)
        self.cwr_interaction += random.randint(2, 8)

        page = {
            "pageId": page_id,
            "interaction": self.cwr_interaction,
            "referrer": "",
            "referrerDomain": "",
            "start": int(time.time() * 1000),
        }

        if parent_page:
            page["parentPageId"] = parent_page

        payload = {
            "sessionId": self.cwr_session_id,
            "record": True,
            "eventCount": self.cwr_event_count,
            "page": page,
        }

        value = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode()

        self.session.cookies.set(
            "cwr_s",
            value,
            domain="auth.hiring.amazon.com",
            path="/",
        )

        return value

    def _call_graphql(
        self,
        *,
        query: str,
        variables: dict,
        operation_name: str,
        headers=None,
        **kwargs: dict,
    ):
        return self.request(
            url='https://jobs.amazon.in/graphql',
            method='POST',
            json={
                'operationName': operation_name,
                'query': query,
                'variables': variables,
            },
            headers={
                'origin': 'https://jobs.amazon.in',
                'referer': 'https://jobs.amazon.in/app',
                **(headers or {})
            },
            **kwargs
        ).json()
