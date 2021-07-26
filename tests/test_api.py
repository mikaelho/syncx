"""
Parts of these tests are intended to be copied directly to docs, thus imports etc. are repeated.
"""


def test_sync__initial_run(run_in_tmp_path):

    my_data = {'value': 'initial'}

    from syncx import sync

    my_data = sync(my_data, 'data.yaml')

    from pathlib import Path
    data_file = Path('data.yaml')

    assert data_file.read_text().strip() == 'value: initial'

    my_data['value'] = 'changed'

    assert data_file.read_text().strip() == 'value: changed'


def test_sync__next_run(run_in_tmp_path):
    from syncx import sync
    sync({'value': 'changed'}, 'data.yaml')

    my_data = sync({'value': 'initial'}, 'data.yaml')
    assert my_data['value'] == 'changed'


def test_sync__json(run_in_tmp_path):
    from pathlib import Path
    from syncx import sync

    my_data = sync({'value': 'initial'}, 'data.json')
    my_data['value'] = 'changed'

    assert Path('data.json').read_text().strip() == '{"value":"changed"}'


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


def test_sync__custom_object(run_in_tmp_path):
    from syncx import sync
    from pathlib import Path
    from types import SimpleNamespace as RandomCustomClass

    my_data = sync(RandomCustomClass(value='initial'), 'data.yaml')
    my_data.value = 'changed'

    assert Path('data.yaml').read_text().strip() == 'value: changed'

    next_run_data = sync(RandomCustomClass(value='initial'), 'data.yaml')

    assert next_run_data.value == 'changed'
    assert type(next_run_data.__subject__) is RandomCustomClass


def test_sync__pydantic_model(run_in_tmp_path, capsys, multiline_cleaner):
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

    order_list = sync(OrderList(), 'data.yaml')
    order = Order(customer_name='Customer', date='2021-07-03')
    order.line_items.append(LineItem(description='Widgets', units=100, amount="1.23"))
    order_list.orders.append(order)

    print(Path('data.yaml').read_text())
    # prints file contents:
    # orders:
    # - customer_name: Customer
    #   date: '2021-07-03'
    #   id: 4a311b41-8e29-4508-9135-d807cc1cb6ef
    #   line_items:
    #   - amount: 1.23
    #     description: Widgets
    #     units: 100

    next_run_order_list = sync(OrderList(), 'data.yaml')

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
