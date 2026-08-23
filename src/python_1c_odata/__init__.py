"""Async client for the 1C:Enterprise standard OData interface (OData 3.0)."""

from python_1c_odata.accumulation_register import AccumulationRegister
from python_1c_odata.catalog import Catalog
from python_1c_odata.client import Infobase
from python_1c_odata.document import Document
from python_1c_odata.errors import ODataError
from python_1c_odata.information_register import InformationRegister
from python_1c_odata.literals import guid, odata_datetime, parse_guid
from python_1c_odata.posting import PostingMode

__version__ = "0.2.1"
__all__ = [
    "AccumulationRegister",
    "Catalog",
    "Document",
    "Infobase",
    "InformationRegister",
    "ODataError",
    "PostingMode",
    "guid",
    "odata_datetime",
    "parse_guid",
]
