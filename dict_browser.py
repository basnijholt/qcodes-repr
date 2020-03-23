from functools import partial

from ipywidgets import Box, Button, GridspecLayout, Label, Layout
from toolz.dicttoolz import get_in


def botton(description, button_style, on_click=None):
    b = Button(
        description=description,
        button_style=button_style,
        layout=Layout(height="auto", width="auto"),
    )
    if on_click is not None:
        b.on_click(on_click)
    return b


def text(description):
    return Label(value=description, layout=Layout(height="max-content", width="auto"))


def _update(nested_keys, table, box, ncols):
    draw = two_columns if ncols == 2 else three_columns

    def _(_):
        box.children = (draw(nested_keys, table, box),)

    return _


def two_columns(nested_keys, table, box):
    update = partial(_update, table=table, box=box, ncols=2)
    selected_table = get_in(nested_keys, table)
    grid = GridspecLayout(len(selected_table) + 1, 30)

    # Header
    title = " ► ".join(nested_keys)
    grid[0, :-1] = botton(title, "success")
    up_click = update(nested_keys[:-1])
    grid[0, -1] = botton("↰", "info", up_click)

    # Body
    for i, (k, v) in enumerate(selected_table.items()):
        grid[i + 1, :10] = botton(k, "warning", up_click)
        if _should_expand(v):
            sub_keys = ", ".join(v.keys())
            grid[i + 1, 10:] = botton(sub_keys, "danger", update([*nested_keys, k]))
        else:
            grid[i + 1, 10:] = text(str(v))
    return grid


def _should_expand(x):
    return isinstance(x, dict) and x != {}


def _row_length(table):
    length = sum(len(v) if _should_expand(v) else 1 for v in table.values())
    return length + 1


def three_columns(nested_keys, table, box):
    update = partial(_update, table=table, box=box, ncols=3)
    col_widths = [8, 16, 30]
    selected_table = get_in(nested_keys, table)
    grid = GridspecLayout(_row_length(selected_table), col_widths[-1])

    # Header
    title = " ► ".join(nested_keys)
    grid[0, :-1] = botton(title, "success")
    up_click = update(nested_keys[:-1])
    grid[0, -1] = botton("↰", "info", up_click)

    # Body
    i = 1
    for k, v in selected_table.items():
        row_length = len(v) if _should_expand(v) else 1
        button = botton(k, "info", up_click)
        grid[i : i + row_length, : col_widths[0]] = button
        if _should_expand(v):
            for k_, v_ in v.items():
                button = botton(k_, "danger", update([*nested_keys, k]))
                grid[i, col_widths[0] : col_widths[1]] = button
                if isinstance(v_, dict) and v_ != {}:
                    sub_keys = ", ".join(v_.keys())
                    button = botton(sub_keys, "warning", update([*nested_keys, k, k_]))
                else:
                    button = text(str(v_))
                grid[i, col_widths[1] :] = button
                i += 1
        else:
            grid[i, col_widths[0] :] = text(str(v))
            i += 1
    return grid


def nested_dict_browser(nested_dict, nested_keys=[], ncols=3):
    box = Box([])
    _update(nested_keys, nested_dict, box, ncols)(None)
    return box
