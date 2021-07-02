# syncx

### "Always saved" as a developer feature

When you use any modern editing tool, were it an IDE or an online office document editor, you
expect the data to be saved as you make changes, without the need to click "Save" every now and
then.

`syncx` gives that same experience for an application developer, automatically saving the application
data whenever it is changed.

### Detect changes

Any change to a wrapped data structure triggers a callback (here we use `print` to keep the example
simple).

```python
import syncx

my_data = {'a': ['b', {'c': 0}]}
my_data = syncx.wrap(my_data, print)
my_data['a'][1]['d'] = 1
# prints: {'c': 0, 'd': 1}
```

Trackable data types: `dict`s (mappings), `list`s (sequences), `set`s, instances with `__dict__`,
others.

### Sync all changes to a YAML file

```python
import syncx
from pathlib import Path

my_data = syncx.sync({'value': 'initial'})

print(Path('syncx_data.yaml').read_text())
# prints file contents:
# value: initial

my_data['value'] = 'changed'

print(Path('syncx_data.yaml').read_text())
# prints file contents:
# value: changed
```

### Next run picks up the changed data

```python
import syncx

my_data = syncx.sync({'value': 'initial'})
assert my_data['value'] == 'changed'
```

(This is already pretty functional for applications with modest amount of data.)

### Use a different serializer

```python
from pathlib import Path
import syncx
from syncx.serializer import JsonSerializer

my_data = syncx.sync({'value': 'initial'}, serializer=JsonSerializer)
my_data['value'] = 'changed'

print(Path('syncx_data.json').read_text())
# prints file contents:
# {"value":"changed"}
```

(Alas, `set` is not supported in json. `ujson` is used if installed.)
