# def application(env, start_response):
#     start_response('200 OK', [('Content-Type'), ('text/html')])
#     return [b"Hellow World"]
import json

import requests
header = {
    'SS-Token': 'b859f200c0ed4ba491f9a4185f6fb64f',
    'Content-Type': 'application/json-patch+json',
    'accept': 'application/json'
}
payload = {
"projectIds": [
    '27316'
  ],
  "includeHidden": True
}
result = requests.post('https://api.survey-studio.com/projects/counters', data=json.dumps(payload), headers=header)
# print(result)
# response = result.json()
print(result)
response = result.json()
for i in range(0,len(response['body'][0]['counters'])-1):
    if response['body'][0]['counters'][i]['value'] == 20:
        print(response['body'][0]['counters'][i])
        print(i)
