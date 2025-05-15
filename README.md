# python-1c-odata

A library for working with 1C through the OData protocol. Supports asynchronous operations with documents, catalogs, and registers.

## Installation

```bash
pip install python-1c-odata
```

## Key Features

- Asynchronous document operations (create, read, post)
- Catalog operations (create, read, update)
- Information and accumulation registers support
- Filtering, selection, and data expansion support

## Usage Examples

```python
import asyncio
from odata.core import Infobase
from odata.document import Document
from odata.catalog import Catalog
from odata.informationregister import InformationRegister

async def main():
    # Connect to 1C
    infobase = Infobase(
        server="http://your-server",
        infobase="your-infobase",
        username="your-username",
        password="your-password"
    )

    # Work with documents
    doc = Document(infobase, "Document")
    docs = await doc.query(
        top=10,
        select="Ref_Key,Number,Date",
        odata_filter="Date ge datetime'2024-01-01T00:00:00'"
    )

    # Work with catalog
    catalog = Catalog(infobase, "Catalog")
    items = await catalog.query(
        top=100,
        select="Ref_Key,Description"
    )

    # Work with register
    register = InformationRegister(infobase, "Register")
    data = await register.slice_last(
        period="2024-03-20T00:00:00",
        select="Period,RecordKey,Value"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Requirements

- Python 3.7+
- aiohttp

## License

MIT
