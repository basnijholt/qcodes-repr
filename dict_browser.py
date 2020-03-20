from ipywidgets import Box, Button, GridspecLayout, Layout
from toolz.dicttoolz import get_in


def create_expanded_button(description, button_style):
    return Button(
        description=description,
        button_style=button_style,
        layout=Layout(height="auto", width="auto"),
    )


def update(nested_keys, table, box):
    def _(_):
        box.children = (draw(nested_keys, table, box),)

    return _


def draw(nested_keys, table, box):
    selected_table = get_in(nested_keys, table)
    grid = GridspecLayout(len(selected_table) + 1, 30)
    title = " ► ".join(nested_keys)
    header = create_expanded_button(title, "success")
    grid[0, :-1] = header
    back_button = create_expanded_button("↰", "info")
    back_button.on_click(update(nested_keys[:-1], table, box))
    grid[0, -1] = back_button
    for i, (k, v) in enumerate(selected_table.items()):
        grid[i + 1, :10] = create_expanded_button(k, "warning")
        if isinstance(v, dict) and v != {}:
            button = create_expanded_button(", ".join(v.keys()), "danger")
            button.on_click(update(nested_keys + [k], table, box))
            grid[i + 1, 10:] = button
        else:
            grid[i + 1, 10:] = create_expanded_button(str(v), "")
    return grid


def nested_dict_browser(nested_dict, nested_keys=[]):
    box = Box([])
    update([], nested_dict, box)(None)
    return box
