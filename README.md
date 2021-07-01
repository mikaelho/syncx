# syncx

### "Always saved" as a developer feature

When you use any modern editing tool, were it an IDE or an online office document editor, you
expect the data to be saved as you make changes, without the need to click "Save" every now and
then.

`syncx` gives that same experience for an application developer, automatically saving the application
data whenever it is changed.

### Detect changes

Any change to a wrapped data structure triggers a callback (here `print`).

```python
>>> import syncx
>>> my_data = {'a': ['b', {'c': 0}]}
>>> my_data = syncx.wrap(my_data, print)
>>> my_data['a'][1]['d'] = 1
{'c': 0, 'd': 1}

```

> Trackable data types: `dict`s (mappings), `list`s (sequences), `set`s, instances with `__dict__`,
> others.

### Sync all changes to YAML file

>>> syncx.sync(my_data)
>>> my_data['e'] = {1}
>>>
>>> from pathlib import Path
>>> Path('syncx_data.yaml').read_text()
a:
- b
- c: 0
  d: 1
e: !!set
  1: null

### Load up data on the next run

>>> my_new_run_data = syncx.sync({'a': 'Default value if no previous data found'})
>>> my_new_run_data['a'][0]
'b'

    Already pretty functional for applications with modest amount of data.

### Use a different serializer

>>> syncx.set_serializer(my_new_run_data, syncx.JsonSerializer)
>>> my_new_run_data['a'][0] = 'f'
>>> Path('synx_default.json').read_text()


    Alas, sets not supported in json.
