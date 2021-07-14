# syncx: autosave for developers

When you use any modern editing tool, were it an IDE or an online office document editor, you
expect the data to be saved as you make changes, without the need to click "Save" every now and
then. `syncx` gives that same experience for an application developer, automatically saving the
application data whenever it is changed.

Main features:
1. Detect changes to Python data structures, from `dict`s to pydantic models.
1. Undo/redo changes.
1. Autosave changes to a file.

## Installation

```
pypi install syncx
```

## Functionality

### Detect changes

Any change to a wrapped data structure triggers a callback.

```python
import syncx

def ping(details):
    print('Data was changed')

my_data = {'a': ['b', {'c': 0}]}
my_data = syncx.tag(my_data, ping)
my_data['a'][1]['d'] = 1
# prints: Data was changed
```

(Supported data types: `dict`s (mappings), `list`s (sequences), `set`s, instances with `__dict__`,
including dataclasses and pydantic models.)

### Move backwards and forwards in the change history

```python
from syncx import tag, manage

my_data = {'value': 'initial'}
my_data = tag(my_data)
manage(my_data).history.on()

my_data['value'] = 'changed'
assert my_data['value'] == 'changed'

manage(my_data).history.undo()
assert my_data['value'] == 'initial'

manage(my_data).history.redo()
assert my_data['value'] == 'changed'
```

(Change history is by default kept in the memory, with no limit on the amount of changes kept.)

### Sync all changes to a YAML file

```python
from syncx import sync
from pathlib import Path

my_data = sync({'value': 'initial'})

print(Path('syncx_data.yaml').read_text())
# prints file contents:
#     value: initial

my_data['value'] = 'changed'

print(Path('syncx_data.yaml').read_text())
# prints file contents:
#     value: changed
```

### Next run picks up the changed data

```python
from syncx import sync

my_data = sync({'value': 'initial'})
assert my_data['value'] == 'changed'
```

(This is already pretty functional for applications with a smallish amount of data.)

### You can use a different serializer

```python
from pathlib import Path
from syncx import sync
from syncx.serializer import JsonSerializer

my_data = sync({'value': 'initial'}, serializer=JsonSerializer)
my_data['value'] = 'changed'

print(Path('syncx_data.json').read_text())
# prints file contents:
#     {"value":"changed"}
```

(Alas, `set` is not supported in json. `ujson` is used if installed.)

### Sync data in "any" object

```python
from syncx import sync
from pathlib import Path
from types import SimpleNamespace as RandomCustomClass

my_data = sync(RandomCustomClass(value='initial'))
my_data.value = 'changed'

print(Path('syncx_data.yaml').read_text())
# prints file contents:
#     value: changed
```

(The object needs to have a `__dict__` attribute and support initialization with a dict of values,
i.e. `RandomCustomClass(**values)`.)

### Sync "strongly-typed" data: Dataclasses and pydantic models

````python
import uuid
import datetime
import decimal
from pathlib import Path
from typing import List

from pydantic import BaseModel

from syncx import sync

class LineItem(BaseModel):
    description: str
    units: int
    amount: decimal.Decimal

class Order(BaseModel):
    id: uuid.UUID = uuid.uuid4()
    customer_name: str
    date: datetime.date = datetime.date.today()
    line_items: List[LineItem] = []

class OrderList(BaseModel):
    orders: List[Order] = []

order_list = sync(OrderList())
order = Order(customer_name='Customer', date='2021-07-03')
order.line_items.append(LineItem(description='Widgets', units=100, amount="1.23"))
order_list.orders.append(order)

print(Path('syncx_data.yaml').read_text())
# prints file contents:
    # orders:
    # - customer_name: Customer
    #   date: '2021-07-03'
    #   id: 4a311b41-8e29-4508-9135-d807cc1cb6ef
    #   line_items:
    #   - amount: 1.23
    #     description: Widgets
    #     units: 100

# On the "next run"
    
order_list = sync(OrderList())

assert order_list.orders[0].customer_name == 'Customer'
````

Notes:

- Dataclasses work as well.
- Pydantic handles types like `datetime`, `decimal` and `uuid` nicely.
- When using strongly-typed data, you need to give `sync` a root model like OrderList in the
  example above. If you give it a list, for example, saving to file will work, but there is not
  enough information to convert the file contents back into an object on the next run.

## Undeveloped ideas

- Support for Django ORM models, with a change callback that saves a Django model to DB
- Use with a UI framework, autoupdate UI whenever data changes
- Peer-to-peer syncing of data

## Do not use syncx when...

- Performance is the main consideration
- Complex queries over large datasets are needed
- Data does not fit in the memory  
- "Magic" code is bad (often same as having a large project)

## Similar projects

- [CleverDict](https://pypi.org/project/cleverdict/)
