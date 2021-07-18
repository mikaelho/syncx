"""
Parts of these tests are intended to be copied directly to docs, thus imports etc. are repeated.
"""


def test_tag(capsys):
    import syncx

    def callback(details):
        print('Data was changed')

    my_data = {'a': ['b', {'c': 0}]}
    my_data = syncx.tag(my_data, callback)
    my_data['a'][1]['d'] = 1
    # prints: Data was changed

    assert capsys.readouterr().out.strip() == "Data was changed"


def test_history():
    from syncx import tag, undo, redo

    my_data = tag({'value': 'initial'}, history=True)

    my_data['value'] = 'changed'
    assert my_data['value'] == 'changed'

    undo(my_data)
    assert my_data['value'] == 'initial'

    redo(my_data)
    assert my_data['value'] == 'changed'


def test_transaction():
    from syncx import tag, rollback

    my_data = tag({'value': 'initial'})

    with my_data:
        my_data['value'] = 'changed'
        rollback()  # This is explicit rollback of any changes; could also be caused by any exception

    assert my_data['value'] == 'initial'


def test_sync__no_previous_file(run_in_tmp_path, capsys, multiline_cleaner):
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

    assert capsys.readouterr().out.strip() == multiline_cleaner(
        """
        value: initial
        
        value: changed"""
    )


def test_sync__next_run(run_in_tmp_path):
    import syncx
    my_data = syncx.sync({'value': 'initial'})
    my_data['value'] = 'changed'

    import syncx

    my_data = syncx.sync({'value': 'initial'})
    assert my_data['value'] == 'changed'


def test_sync__with_json(run_in_tmp_path, capsys):
    from pathlib import Path
    import syncx
    from syncx.serializer import JsonSerializer

    my_data = syncx.sync({'value': 'initial'}, serializer=JsonSerializer)
    my_data['value'] = 'changed'

    print(Path('syncx_data.json').read_text())
    # prints file contents:
    # {"value":"changed"}

    assert capsys.readouterr().out.strip() == '{"value":"changed"}'


def test_sync__custom_object(run_in_tmp_path, capsys):
    import syncx
    from pathlib import Path
    from types import SimpleNamespace as RandomCustomClass

    my_data = syncx.sync(RandomCustomClass(value='initial'))
    my_data.value = 'changed'

    print(Path('syncx_data.yaml').read_text())
    # prints file contents:
    # value: changed

    assert capsys.readouterr().out.strip() == 'value: changed'


def test_sync__pydantic_model(run_in_tmp_path, capsys, multiline_cleaner):
    import uuid
    import datetime
    import decimal
    from pathlib import Path
    from typing import List

    from pydantic import BaseModel

    import syncx

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

    order_list = syncx.sync(OrderList())
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

    next_run_order_list = syncx.sync(OrderList())

    assert next_run_order_list.orders[0].customer_name == 'Customer'

    assert capsys.readouterr().out.strip() == multiline_cleaner(
        f"""
        orders:
        - customer_name: Customer
          date: '2021-07-03'
          id: {order.id}
          line_items:
          - amount: 1.23
            description: Widgets
            units: 100"""
    )
