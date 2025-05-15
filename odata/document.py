import json

import aiohttp
from odata.core import make_url_part
from odata.postingmode import PostingMode


class Document:
    def __init__(self, infobase, docname):
        self.infobase = infobase
        self.docname = docname
        self.url = self.infobase._full_url.format(obj='Document_' + self.docname)

    async def query(self, top=None, skip=None, select=None, odata_filter=None, expand=None, orderby=None, timeout=None):
        _url_top = await make_url_part('top', top, int)
        _url_skip = await make_url_part('skip', skip, int)
        _url_select = await make_url_part('select', select, str)
        _url_filter = await make_url_part('filter', odata_filter, str)
        _url_expand = await make_url_part('expand', expand, str)
        _url_orderby = await make_url_part('orderby', orderby, str)

        url = self.url + _url_top + _url_skip + _url_select + _url_filter + _url_expand + _url_orderby

        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, url, timeout)

    async def get(self, guid, select=None, timeout=None):
        obj = "Document_{}(guid'{}')".format(self.docname, guid)
        url = self.infobase._full_url.format(obj=obj)

        _url_select = await make_url_part('select', select, str)
        url = url + _url_select

        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, url, timeout)

    async def post(self, guid, posting_mode, timeout=None):
        obj = f"Document_{self.docname}(guid'{guid}')/Post"
        url = self.infobase._full_url.format(obj=obj)
        params = {}
        if posting_mode == PostingMode.OPER:
            params['PostingModeOperational'] = 'true'
        elif posting_mode == PostingMode.POST:
            params['PostingModeOperational'] = 'false'
        else:
            raise ValueError('Use unpost_document() for unposting')

        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=self.infobase._auth, headers=self.infobase._headers, params=params,
                                    timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(await response.text())

    async def unpost(self, guid, timeout=None):
        obj = f"Document_{self.docname}(guid'{guid}')/Unpost"
        url = self.infobase._full_url.format(obj=obj)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=self.infobase._auth, headers=self.infobase._headers,
                                    timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(await response.text())

    async def edit(self, guid, data, timeout=None):
        if 'Posting' in data:
            raise ValueError('Do not pass the "Posting" field')

        obj = f"Document_{self.docname}(guid'{guid}')"
        url = self.infobase._full_url.format(obj=obj)

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, auth=self.infobase._auth, headers=self.infobase._headers,
                                     data=json.dumps(data), timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(await response.text())
                return await response.json()

    async def create(self, data, posting_mode=PostingMode.UNPOST, timeout=None):
        if ('Posting' in data) and (data['Posting'] == True):
            raise ValueError('Do not pass the "Posting" field')
        if 'Date' not in data:
            raise ValueError('Date value cannot be an empty date')

        url = self.url
        async with aiohttp.ClientSession() as session:
            async with session.post(url, auth=self.infobase._auth, headers=self.infobase._headers,
                                    data=json.dumps(data), timeout=timeout) as response:
                if response.status != 201:
                    raise Exception(await response.text())

                new_doc = await response.json()

                if posting_mode != PostingMode.UNPOST:
                    await self.post(new_doc['Ref_Key'], posting_mode, timeout)

                return new_doc
