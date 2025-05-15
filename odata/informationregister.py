import aiohttp
from odata.core import Infobase, make_url_part


class InformationRegister:
    infobase: Infobase

    def __init__(self, infobase, regname):
        self.infobase = infobase
        self.regname = regname
        self.url = self.infobase._full_url.format(obj='InformationRegister_' + self.regname)

    async def query(self, top=None, skip=None, select=None, odata_filter=None, expand=None, timeout=None):
        _url_top = await make_url_part('top', top, int)
        _url_skip = await make_url_part('skip', skip, int)
        _url_select = await make_url_part('select', select, str)
        _url_filter = await make_url_part('filter', odata_filter, str)
        _url_expand = await make_url_part('expand', expand, str)
        url = self.url + _url_top + _url_skip + _url_select + _url_filter + _url_expand

        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, url, timeout)

    async def slice_last(self, period=None, condition=None, select=None, orderby=None, expand=None, timeout=None):
        _url_select = await make_url_part('select', select, str)
        _url_orderby = await make_url_part('orderby', orderby, str)
        _url_expand = await make_url_part('expand', expand, str)
        period_value = '' if period is None else period
        condition_value = '' if condition is None else condition

        full_url = (self.infobase._full_url.format(
            obj='InformationRegister_' + self.regname + f'/SliceLast({period_value},{condition_value})')) + f'{_url_select}{_url_orderby}{_url_expand}'

        async with aiohttp.ClientSession() as session:
            return await self.infobase.fetch_data(session, full_url, timeout)
