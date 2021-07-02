"""
Parts of these tests are intended to be copied directly to docs, thus imports etc. are repeated.
"""
import syncx


def test_wrap(capsys):
    import syncx

    my_data = {'a': ['b', {'c': 0}]}
    my_data = syncx.wrap(my_data, print)
    my_data['a'][1]['d'] = 1
    # prints: {'c': 0, 'd': 1}

    assert capsys.readouterr().out.strip() == "{'c': 0, 'd': 1}"


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
