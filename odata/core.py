import json

import aiohttp


class Infobase:
    _headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Connection': 'keep-alive'}

    server: str
    infobase: str
    _full_url: str
    _auth: aiohttp.BasicAuth

    def __init__(self, server, infobase, username, password):
        self.server = server
        self.infobase = infobase
        self._full_url = server + infobase + '/odata/standard.odata/{obj}?$format=json'
        self._auth = aiohttp.BasicAuth(username, password, encoding='utf-8')

    async def fetch_data(self, session, url, timeout):
        async with session.get(url, auth=self._auth, headers=self._headers, timeout=timeout) as response:
            response_text = await response.text()
            response_text = json.loads(response_text)
            return response_text


async def make_url_part(name, value, value_type):
    if value == None:
        return ''
    if type(value) != value_type:
        raise ValueError('{}={} must be {}'.format(name, value, value_type))
    result = "&${}={}".format(name, value)
    return result
