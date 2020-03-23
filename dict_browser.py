from functools import partial

from ipywidgets import Box, Button, GridspecLayout, Label, Layout
from toolz.dicttoolz import get_in


def button(description, button_style, on_click=None):
    but = Button(
        description=description,
        button_style=button_style,
        layout=Layout(height="auto", width="auto"),
    )
    if on_click is not None:
        but.on_click(on_click)
    return but


def text(description):
    return Label(value=description, layout=Layout(height="max-content", width="auto"))


def _update(nested_keys, table, box):
    def _(_):
        box.children = (draw_table(nested_keys, table, box),)

    return _


def _should_expand(x):
    return isinstance(x, dict) and x != {}


def draw_table(nested_keys, table, box, max_nrows=30):
    col_widths = [8, 16, 30]
    selected_table = get_in(nested_keys, table)
    nrows = sum(len(v) if _should_expand(v) else 1 for v in selected_table.values()) + 1
    ncols = 3
    if nrows > max_nrows:
        nrows = len(selected_table) + 1
        col_widths.pop(1)
        ncols = 2
    grid = GridspecLayout(nrows, col_widths[-1])
    update = partial(_update, table=table, box=box)

    # Header
    title = " ► ".join(nested_keys)
    grid[0, :-1] = button(title, "success")
    up_click = update(nested_keys[:-1])
    grid[0, -1] = button("↰", "info", up_click)

    # Body
    if ncols == 3:
        i = 1
        for k, v in selected_table.items():
            row_length = len(v) if _should_expand(v) else 1
            but = button(k, "info", up_click)
            grid[i : i + row_length, : col_widths[0]] = but
            if _should_expand(v):
                for k_, v_ in v.items():
                    but = button(k_, "danger", update([*nested_keys, k]))
                    grid[i, col_widths[0] : col_widths[1]] = but
                    if isinstance(v_, dict) and v_ != {}:
                        sub_keys = ", ".join(v_.keys())
                        but = button(sub_keys, "warning", update([*nested_keys, k, k_]))
                    else:
                        but = text(str(v_))
                    grid[i, col_widths[1] :] = but
                    i += 1
            else:
                grid[i, col_widths[0] :] = text(str(v))
                i += 1
    else:
        for i, (k, v) in enumerate(selected_table.items()):
            grid[i + 1, : col_widths[0]] = button(k, "info", up_click)
            if _should_expand(v):
                sub_keys = ", ".join(v.keys())
                grid[i + 1, col_widths[0] :] = button(
                    sub_keys, "danger", update([*nested_keys, k])
                )
            else:
                grid[i + 1, col_widths[0] :] = text(str(v))
    return grid


def nested_dict_browser(nested_dict, nested_keys=[]):
    box = Box([])
    _update(nested_keys, nested_dict, box)(None)
    return box
