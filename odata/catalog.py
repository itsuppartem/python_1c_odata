import aiohttp
from odata.core import Infobase, make_url_part


class Catalog:
    infobase: Infobase
    url: str

    def __init__(self, infobase, cat_name):
        self.infobase = infobase
        self.cat_name = cat_name
        self.url = self.infobase._full_url.format(obj='Catalog_' + self.cat_name)

    async def get(self, guid, select=None, timeout=None):
        obj = "Catalog_{}(guid'{}')".format(self.cat_name, guid)
        url = self.infobase._full_url.format(obj=obj)

        _url_select = await make_url_part('select', select, str)
        url = url + _url_select

        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, url, timeout)

    async def query(self, top=None, skip=None, select=None, odata_filter=None, expand=None, timeout=None):
        _url_top = await make_url_part('top', top, int)
        _url_skip = await make_url_part('skip', skip, int)
        _url_select = await make_url_part('select', select, str)
        _url_filter = await make_url_part('filter', odata_filter, str)
        _url_expand = await make_url_part('expand', expand, str)
        url = self.url + _url_top + _url_skip + _url_select + _url_filter + _url_expand
        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, url, timeout)

    async def create(self, data, timeout=None):
        url = self.url
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, auth=self.infobase._auth, headers=self.infobase._headers,
                                    timeout=timeout) as resp:
                print(resp)
                return await resp.json()

    async def edit(self, guid, data, timeout=None):
        obj = f"Catalog_{self.cat_name}(guid'{guid}')"
        url = self.infobase._full_url.format(obj=obj)

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data, auth=self.infobase._auth, headers=self.infobase._headers,
                                     timeout=timeout) as resp:
                if resp.status != 200:
                    raise Exception(await resp.text())
                return await resp.json()
