import json
from datetime import datetime, timezone, timedelta
import random
from time import sleep
import urllib.parse
import websocket

from logger import Logger
from network import USER_AGENT, AmazonRequest, BaseRequest
from graphql_quires import JOB_SEARCH_BY_LOCATION
from utils import search_regex
from utils._utils import url_or_none
from utils.traversal import traverse_obj
from models import evaluate_question, evaluate_scale_question, evaluate_item_code
from searcher import UKMapSearcher

class AmazonJob(
    AmazonRequest,
    Logger
  ):
    def __init__(self, req: BaseRequest, region='UK'):
        super().__init__(req, region)
        self.HVH_ACCESS_TOKEN = 'AQICAHgRVX6yB5HaOXG/6jWEErD4AnJUVlc3se+5PoiAFFV3IgFYzf2LfRAQPXehwGeDKUZRAAAEkzCCBI8GCSqGSIb3DQEHBqCCBIAwggR8AgEAMIIEdQYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxdHiHXWEMTKiUWmBwCARCAggRGNnospziUhMwTk/LEiyTu6ZXvfaHCmSTDz2KWN/pTenTq8yzwZdx54xmA7Al+zVOy+/MnOfckHGia6XoRgQrJtmRsS143/cL0ZCa0VvFbkgMJwD3eewSp3bDlWUwoKmD8ZAk5DT8JEAbgglcUJTuNDYxXaPWN1Ts6bsSeTBdFDUaeyOi4G1nTq68Zx2R1OyWtD2/KfpT3gSbCBkRAF2JFVEYWwYhEPMUJE/l52py64yEBP0OfWTdQyd1iLtwxZZfRyv8yoQQbkzaGnO7OfwejHN7tAmVte57XMHjbjWj43hI/J41s03PBhkaOeddFEuMMkukTfb2PoDX1rahmfXmg09XP1dBVleLEggxDyBqY1kJ2t3yx0ZmapiSU3Dz7JRDu+KHnXZEbThjXNpQ3RCtTERuMKEzV5hMawsAT7nSti19TcOmEbQdWNJK3NnKa0sPVOLehuSmtz/JxOGdIKpDrNjES0whKiNRAID1RB6WOwnY0GnnLB5rwy1D7qdxmxIt0VUz/E3OGlG2UhZ8sJjBG9d75IBoqk4tv3yQJnNOKxkIRnBgZRsB/Dr0Pp6wrDSsHm4yrOr7+8LZuA/RnPmF8jKyRS8hF02NqLXHPvb7TjECaVtqAl06Cu2y9es4e2kauzgE4WgtCYj5M/bRMHrmKnAHfjy64byeA4KFbEWKJ/FOQfq9eQ9RAhYSmbWtFPju6YY3vfJDux5mX4aLxzf163BPBONgWE6MwGsCzS2nSjKZ0dPJo+r3Xoq0OfaYtCGJ5OwK0N/SwJgzFGBJe1m4fFBAHbQ8xWnKyuYb8rEZuQyb0Ed8zPXubG4gbRVu9zSswjIPtY7gMFlxFswnkmda4K8WEoY/aSimS+D5z/SQqI8cfVR1yttka+Mq5sILyfM1Bv2BWi7br/IAiTIhBtp7i1XHS3jbR4zWcoGGboR7pnrceL+2sqXBaz+2804DdBI8fN5NMHVoOyW6MscngsXafnzJBDatW0IEHpiXgTVBw7brAvALETOkJLt1D7lQWAhxBSJTJUwzJFZgpqPzfpoVLE0Ma/NXStJ96bvl/iOXj69APZZrWcGkVHCS0ITGY5Hqja9gA1T7E+UFoh5lD7a4pYaza/a/z7rVfK+coXoq06uOZUrCkUU5OG48qs8xHEi6lMDNqAMbIH3uucS7zpbfDjJX4xpt6k2m6UL+SOZBNUpTCFXha+Bj78VE2QvJCmUlKogePqqiSUglCpxjK/co0y+rnFV3Yvu1kkqocBasm1i8YkzrOpYCSQXSxo01MZlokMtrXMlU09JdNoxQeRzUGJAE6meKNxBiNIv1CJ/SiMAS30x39D8oVuCkcSyCIQi96pMV7coV0awKAlQt5DCAfFYvBbbqwfoRqWdEeCDQyca0vCKPiRCzPEpP4ad/JHsSbKrT9bXYKuJrFlGQJ3zB6NvnJzT9ifBYNg8GJ9Rxa7uiEp5jq+Hw='
        self.session.cookies.update({'HVH_ACCESS_TOKEN': self.HVH_ACCESS_TOKEN})
        self._get_csrf()
        self.searcher = UKMapSearcher()
        self.session.headers.update({'Authorization': f'Bearer Status|logged-in|Session|{self.csrf}'})
        self._DEFAULT_SHIFT_PREF = {
          "earliestStartDate": "13/08/2026",
          "preferredDaysToWork": ["Sat", "Mon", "Sun", "Tue", "Wed", "Thu", "Fri"],
          "hoursPerWeek": [
            { "maximumValue": 40, "minimumValue": 36 },
            { "minimumValue": 0, "maximumValue": 15 },
            { "minimumValue": 25, "maximumValue": 35 },
            { "minimumValue": 15, "maximumValue": 24 }
          ],  
          "shiftTimePattern": "Any"
        }

    def search_job(self, variables: dict):
        data = self._call_graphql(
            query=JOB_SEARCH_BY_LOCATION,
            variables=variables,
            operation_name='searchJobCardsByLocation',
        )['data']['searchJobCardsByLocation']
        jobs =  data['jobCards']
        return jobs

    def _get_job_details(self, job_id):
      return self.call_application_api(f'job/{job_id}')

    @staticmethod
    def current_date():
      return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def call_application_api(self, path, payload=None, headers=None, method=None, **kwargs):
      headers = {'Authorization': self.HVH_ACCESS_TOKEN, **(headers or {})}

      if method is None:
        if payload:
          method = 'POST'
          headers.update({
            'Content-Type': 'application/json;charset=UTF-8',
            'bb-ui-version': 'bb-ui-v2',
          })
        else:
          method = 'GET'

      response =  self.request(
        url=f'https://www.jobsatamazon.co.uk/application/api/{path}',
        method=method,
        json=payload,
        headers=headers,
        **kwargs
      ).json()

      return response.get('data') or response

    def _init_workflow(self, job_id, app_data):
      
      app_id = app_data.get('applicationId')
      cad_id = app_data.get('candidateId')
  
      common = {
        "applicationId": app_id,
        "candidateId": cad_id,
      }
      ws = websocket.WebSocket()
      self.wfws = ws
      ws.connect(
        "wss://www.jobsatamazon.co.uk/application-workflow/?" + urllib.parse.urlencode({
          **common,
          "authToken": self.HVH_ACCESS_TOKEN,
        }),
        origin='https://www.jobsatamazon.co.uk',
        header=[
            f"User-Agent: {USER_AGENT}"
        ],
        cookie="; ".join(
          f"{k}={v}"
          for k, v in self.session.cookies.get_dict().items()
        ),
      )
      payload = {
        'action': 'startWorkflow',
        **common,
        'jobId': job_id,
        'partitionAttributes': { "countryCodes": ["UK"], "ownerOrgs": ["AMZN_WFS"] },
        'filteringSeasonal': False,
        'filteringRegular': False,
        'domainType': 'CS'
      }
      ws.send(json.dumps(payload))
      self._ws_drain_all_messages()

    def _update_workflow_name_with_ws(self, job_detail, app_data, currentWorkflowStep):
      self.wfws.send(json.dumps({
        'action': 'completeTask',
        'currentWorkflowStep': currentWorkflowStep,
        **traverse_obj(app_data, {
          'applicationId': ('applicationId', {str}),
          'candidateId': ('candidateId', {str}),
          'partitionAttributes': ('partitionAttributes', {dict}),
        }),
        **traverse_obj(job_detail, {
          'state': (('geoClusterRegion', 'geoClusterZone'), {str}, any),
        }),
        'workflowStepName': '',
        'filteringRegular': False,
        'filteringSeasonal': False,
        'jobSelectedOn': self.current_date(),
        'employmentType': 'Seasonal',
        'domainType': 'CS',
        'eventSource': 'HVH-CA-UI',
        'requisitionId': '',
      }))
      self._ws_drain_all_messages()

    def _ws_drain_all_messages(self):
      self.wfws.settimeout(2.0)
      while True:
          try:
              self.wfws.recv()
          except websocket.WebSocketTimeoutException:
              break

    def _update_workflow_name_with_api(self, app_id, workflowStepName):
      self.call_application_api(
        'candidate-application/update-workflow-step-name',
        payload={
          'applicationId': app_id,
          'workflowStepName': workflowStepName
        },
        method='PUT'
      )

    def _user_info(self):
      return ...
  
    def apply_job(self, job_id):
      self.info('Applying JOb for {}'.format(self.HVH_ACCESS_TOKEN))
      job_details = self._get_job_details(job_id)
      capp_data = self.call_application_api(
        'candidate-application/ds/create-application/',
        payload={
          "jobId": job_id.upper(),
          "dspEnabled":True,
          "jobAssessmentToggle":False,
          "jobAssessmentType":"Tier1_NextGen_EU_Kondo"
        }
      )
      errorCode = capp_data.get('errorCode') or ''
      if errorCode.lower() == 'APPLICATION_ALREADY_EXIST'.lower():
        return

      candidate = self.candidate()
      app_id = capp_data.get('applicationId')
      self._init_workflow(job_id, capp_data)

      if not bool(traverse_obj(candidate, ('assessmentsTaken', 'Tier1_NextGen_EU_Kondo', lambda x, y: x == 'assessmentStatus' and y == 'Completed', any))):
        self._update_workflow_name_with_ws(job_details, capp_data, 'assessment')
        self._update_workflow_name_with_api(app_id, 'assessment')
        self.step_1_assessment(candidate)

      self._update_workflow_name_with_api(app_id, 'job-opportunities')
      self._init_workflow(job_id, capp_data)
      site_id = self.step_2(job_id, app_id, candidate)
      self._update_workflow_name_with_ws(job_details, capp_data, 'job-opportunities')
      self.info(f'Job site ID {site_id}')

      self.update_application({
        "applicationId": app_id,
        "dspEnabled": True,
        "payload": { "extendedTimestamp": (candidate.get('contingentOffer', {}) or {}).get('extendedTimestamp') or self.current_date()},
        "type": "contingent-offer",
      })
      self._update_workflow_name_with_ws(job_details, capp_data, 'contingent-offer')
      self._init_workflow(job_id, capp_data)
      self._update_workflow_name_with_api(app_id, 'contingent-offer')

      candidate = self.candidate()
      self.step_3(app_id, candidate)
      self._update_workflow_name_with_ws(job_details, capp_data, 'additional-information')
      self._init_workflow(job_id, capp_data)
      self._update_workflow_name_with_api(app_id, 'additional-information')
      today = datetime.today()
      avaliable_slot = random.choice(
        self.call_application_api('nhe/available-time-slots', payload={
          'startDate': today.strftime("%Y-%m-%d"),
          'endDate': (today + timedelta(days=7)).strftime("%Y-%m-%d"),
          'locale': 'en-GB',
          'returnNestedData': True,
          'siteId': site_id,
        })
      )
      self.info(f'Avaiable Slot {avaliable_slot}')
      self.update_application({
        'applicationId': app_id,
        'payload': {
          'nheAppointment': {
            **avaliable_slot
          }
        },
        "type": "nhe",
        "dspEnabled": True
      })
      self._update_workflow_name_with_ws(job_details, capp_data, 'nhe')
      self._init_workflow(job_id, capp_data)
      self._update_workflow_name_with_api(app_id, 'nhe')
      self.update_application({
        'applicationId': app_id,
        'type': 'calculate-inclined-value'
      })
      self._update_workflow_name_with_ws(job_details, capp_data, 'review-submit')
      self._init_workflow(job_id, capp_data)
      self._update_workflow_name_with_api(app_id, 'review-submit')

      self._update_workflow_name_with_ws(job_details, capp_data, 'thank-you')
      self._init_workflow(job_id, capp_data)
      self._update_workflow_name_with_api(app_id, 'thank-you')

      self.update_application({
        'applicationId': app_id,
        'dspEnabled': True,
        'payload': {
          'niFairEmploymentMonitoring':{
            'responseStatus': 'DECLINED',
            'submittedAt': self.current_date(),
          }
        },
        'type': 'ni-fair-employment-monitoring'
      })

    def candidate(self) -> dict:
      return self.call_application_api('candidate-application/candidate')

    def call_assessment_api(self, path, payload=None, headers=None, query=None, method=None, is_json=True, **kwargs):
      query = {'auth': self.assessment_auth, **(query or {})}
      if method is None:
        if payload is not None:
          method = 'POST'
        else:
          method = 'GET'

      self.session.headers.update({'x-client-device-type': 'desktop', **(headers or {})})
      self.session.cookies.update({'auth': self.assessment_auth})
      response = self.request(url=f'https://assessments.amazon.jobs/{path}', method=method, json=payload, params=query, **kwargs)
      return response.json() if is_json else response

    def update_application(self, payload, **kwargs):
      self.call_application_api('candidate-application/update-application', payload=payload, method='PUT', **kwargs)

    def step_1_assessment(self, candidate: dict = None):
      def submit():
        return self.call_assessment_api(f'moduleInstances/{moduleInstanceId}/submit', payload={})

      def send_responses(responses, moduleInstanceId):
        return self.call_assessment_api(
          f'moduleInstances/{moduleInstanceId}/responses',
          payload={'responses': responses},
          method='PUT',
          is_json=False,
        )

      assessment_url = traverse_obj(candidate or self.candidate(), ('assessmentsTaken', ..., 'assessmentUrl', {url_or_none}, any))
      self.assessment_auth, self.workflow_id = search_regex(
        r'http?s://assessments\.amazon\.jobs/?\?auth=([^/#]+)(?:[^#]+)?#/?(?:[^/]+/){2,}(\w+_(?:[a-z0-9-]+))', 
        assessment_url, default=[None, None], group=(1, 2))

      while True:
        workflow_detail = self.call_assessment_api(f'workflowInstances/{self.workflow_id}')
        moduleInstanceId = traverse_obj(workflow_detail, ('workflowInstance', 'steps', ..., 'currentActivity', 'launch', 'moduleInstanceId', {str}, any))

        if not moduleInstanceId:
          break

        while True:
          items = self.call_assessment_api(f'moduleInstances/{moduleInstanceId}/items')
          itemList = traverse_obj(items, ('itemsList', ..., ..., {
            'content': ('content', {json.loads}),
            'itemId': ('itemId', {str}),
            'versionId': ('versionId', {str}),
            'type': ('type', {str})
          }))

          responses = []
          for item in itemList:
            values = []
            item_id = item.get('itemId')
            version_id = item.get('versionId')

            content = item.get('content')
            question = traverse_obj(content, ('question'))
            if question:
              values.append(evaluate_question(question))

            rows = traverse_obj(content, ('rows', {list}, 0, {list}))
            if rows:
              values.append(evaluate_scale_question(rows))

            is_slot = (content.get('contentType') or '') == 'SlotPicker'
            if is_slot:
              values.append(evaluate_item_code(content))

            responses.append({
                'isPartial': False,
                'itemId': item_id,
                'itemVersionId': version_id,
                'metadata': '',
                'values': values
            })

          send_responses(responses, moduleInstanceId)

          if items.get('endOfWorkflow'):
            submit()
            break
        break

    def step_2(self, job_id: str, app_id, candidate: dict = None):
      candidate = candidate or self.candidate()
      if candidate.get('shiftPreferences'):
        ran_shift = None
        while True:
          shifts = traverse_obj(
            self.call_application_api(
              f'job/get-all-schedules/{job_id}',
              payload={
                "jobId": job_id,
                "applicationId": app_id,
                "filter": {
                  "sortBy": "SHIFT_SCHEDULES_SORT",
                  "filter": {
                    "range": {
                      "HOURS_PER_WEEK": {
                        "maximumValue": 100,
                        "minimumValue": 0
                      }
                    },
                    "schedulePreferences": {
                      "MONDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "TUESDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "WEDNESDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "THURSDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "FRIDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "SATURDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      },
                      "SUNDAY": {
                        "startTime": "00:00",
                        "endTime": "23:59"
                      }
                    },
                    "in": {},
                    "eq": {}
                  },
                  "seasonalOnly": False,
                  "locale": "en-GB",
                  "pageFactor": 1,
                  "isCRSJobsDisplayed": True
                },
                "locale": "en-GB"
              }
            ),
            ('availableSchedules', 'schedules', ..., {dict})
          )

          if not shifts:
            self.warn(f'No Shift Available')
            continue
          if shifts:
            ran_shift = shifts[0]
            break

        #Use USER Shift PREF
        scheduleId = ran_shift.get('scheduleId')
        self.info(f'Shift ID {scheduleId}')
        site_id = traverse_obj(ran_shift, ('partitionAttributes', 'siteIds', ..., {str}, any))
        self.update_application({
          "applicationId": app_id,
          "dspEnabled": True,
          "payload": {
            "jobId": job_id,
            "scheduleId": scheduleId
          },
          "type": "job-confirm",
        })
        return site_id

      self.call_application_api('candidate-application/candidate/shiftPreferences', payload=self._DEFAULT_SHIFT_PREF)
      self.step_2(job_id, app_id, self.candidate())
      return True

    #Need some checking and Fix
    def step_3(self, app_id: str, candidate: dict = None):
      candidate = candidate or self.candidate()

      if details := traverse_obj(candidate, (lambda _, x: x['additionalBackgroundInfo']['address'], 'additionalBackgroundInfo')):
        self.update_application({
          'applicationId': app_id,
          'payload':{
            'candidate': {
              **details
            },
            "jobReferral": { "hasReferral": "no" }
          },
          "type": "additional-information",
          "dspEnabled": True
        })
        return True
      #Update Workflow additional-information
      ...

    @staticmethod
    def _fix_multple_loc(address):
      if '/' not in address:
        return
      return address.split('/')[0]

    def _search_apply(self, location='london', radius=50):
      while True:
        self.info(f'Starting Search for Job near {location}')
        try:
          london_job_id = traverse_obj(
            self.search_job({
              "searchJobRequest": {
                "locale": "en-GB",
                "country": "United Kingdom",
                "keyWords": "",
                "equalFilters": [],
                "containFilters": [
                  { "key": "isPrivateSchedule", "val": ["true", "false"] }
                ],
                "rangeFilters": [],
                "orFilters": [],
                "dateFilters": [],
                "sorters": [{ "fieldName": "totalPayRateMax", "ascending": "false" }],
                "pageSize": 100,
                "consolidateSchedule": True
              }
            }), (lambda _, x: self.searcher.is_within_radius(location, radius, self._fix_multple_loc(x.get('locationName')) or self._fix_multple_loc(x['geoClusterDescription'])), 'jobId', {str.upper}, any))
          if london_job_id:
            print(london_job_id)
            self.apply_job(london_job_id)
            return
          self.warn("No matching jobs found. Retrying in 5 seconds...")
          sleep(5)
        except Exception as e:
          self.error(f'Search failed {e}')


#Second Method of Apply Job 
class AmazonHvrJob(BaseRequest):
  def __init__(self, req: BaseRequest) -> None:
    super().__init__(req.session)


amazonJob = AmazonJob(BaseRequest())
amazonJob._search_apply()
