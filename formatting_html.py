import uuid
from functools import partial
from html import escape

import pkg_resources
import pandas as pd

from formatting import format_array_flat, short_numpy_repr

CSS_FILE_PATH = "/".join(("static", "css", "style.css"))
# CSS_STYLE = pkg_resources.resource_string("xarray", CSS_FILE_PATH).decode("utf8")

with open("static/css/style.css") as f:
    CSS_STYLE = "\n".join(f.readlines())

ICONS_SVG_PATH = "/".join(("static", "html", "icons-svg-inline.html"))
ICONS_SVG = pkg_resources.resource_string("xarray", ICONS_SVG_PATH).decode("utf8")


def summarize_attrs(attrs):
    attrs_dl = "".join(
        f"<dt><span>{escape(k)} :</span></dt>" f"<dd>{escape(str(v))}</dd>"
        for k, v in attrs.items()
    )

    return f"<dl class='qc-attrs'>{attrs_dl}</dl>"


def collapsible_section(
    name, inline_details="", details="", n_items=None, enabled=True, collapsed=False
):
    # "unique" id to expand/collapse the section
    data_id = "section-" + str(uuid.uuid4())

    has_items = n_items is not None and n_items
    n_items_span = "" if n_items is None else f" <span>({n_items})</span>"
    enabled = "" if enabled and has_items else "disabled"
    collapsed = "" if collapsed or not has_items else "checked"
    tip = " title='Expand/collapse section'" if enabled else ""

    return (
        f"<input id='{data_id}' class='qc-section-summary-in' "
        f"type='checkbox' {enabled} {collapsed}>"
        f"<label for='{data_id}' class='qc-section-summary' {tip}>"
        f"{name}:{n_items_span}</label>"
        f"<div class='qc-section-inline-details'>{inline_details}</div>"
        f"<div class='qc-section-details'>{details}</div>"
    )


def _icon(icon_name):
    # icon_name should be defined in qcodes-repr/static/html/icon-svg-inline.html
    return (
        "<svg class='icon qc-{0}'>"
        "<use xlink:href='#{0}'>"
        "</use>"
        "</svg>".format(icon_name)
    )


def _obj_repr(header_components, sections):
    header = f"<div class='qc-header'>{''.join(h for h in header_components)}</div>"
    sections = "".join(f"<li class='qc-section-item'>{s}</li>" for s in sections)

    return (
        "<div>"
        f"{ICONS_SVG}<style>{CSS_STYLE}</style>"
        "<div class='qc-wrap'>"
        f"{header}"
        f"<ul class='qc-sections'>{sections}</ul>"
        "</div>"
        "</div>"
    )


def format_dims(dims):
    if not dims:
        return ""

    dim_css_map = {
        k: " class='qc-has-index'" if len(v) != 1 else "" for k, v in dims.items()
    }

    dims_li = "".join(
        f"<li><span{dim_css_map[dim]}>" f"{escape(dim)}</span>: {len(values)}</li>"
        for dim, values in dims.items()
    )

    return f"<ul class='qc-dim-list'>{dims_li}</ul>"


def dim_section(dims):
    dim_list = format_dims(dims)

    return collapsible_section(
        "Sweep parameters", inline_details=dim_list, enabled=False, collapsed=True
    )


def summarize_coord(name, var):
    return {name: summarize_variable(name, **var)}


def summarize_vars(variables):
    vars_li = "".join(
        f"<li class='qc-var-item'>{summarize_variable(k, **v)}</li>"
        for k, v in variables.items()
    )

    return f"<ul class='qc-var-list'>{vars_li}</ul>"


def summarize_coords(variables):
    coords = {}
    for k, v in variables.items():
        coords.update(**summarize_coord(k, v))

    vars_li = "".join(f"<li class='qc-var-item'>{v}</li>" for v in coords.values())

    return f"<ul class='qc-var-list'>{vars_li}</ul>"


def short_data_repr_html(array):
    """Format "data" for DataArray and Variable."""
    return escape(short_numpy_repr(array))


def inline_variable_array_repr(array, max_width):
    return format_array_flat(array, max_width)


def summarize_variable(name, array, attrs, dtype=None, preview=None):
    dims_str = f"({', '.join(escape(dim) for dim in attrs['depends_on'])})"
    name = escape(name)
    dtype = dtype or escape(str(array.dtype))

    # "unique" ids required to expand/collapse subsections
    attrs_id = "attrs-" + str(uuid.uuid4())
    data_id = "data-" + str(uuid.uuid4())
    disabled = "" if len(attrs) else "disabled"

    preview = preview or escape(inline_variable_array_repr(array, 35))
    attrs_ul = summarize_attrs(attrs)
    data_repr = short_data_repr_html(array)

    attrs_icon = _icon("icon-file-text2")
    data_icon = _icon("icon-database")

    return (
        f"<div class='qc-var-name'><span>{name}</span></div>"
        f"<div class='qc-var-dims'>{dims_str}</div>"
        f"<div class='qc-var-dtype'>{dtype}</div>"
        f"<div class='qc-var-preview qc-preview'>{preview}</div>"
        f"<input id='{attrs_id}' class='qc-var-attrs-in' "
        f"type='checkbox' {disabled}>"
        f"<label for='{attrs_id}' title='Show/Hide attributes'>"
        f"{attrs_icon}</label>"
        f"<input id='{data_id}' class='qc-var-data-in' type='checkbox'>"
        f"<label for='{data_id}' title='Show/Hide data repr'>"
        f"{data_icon}</label>"
        f"<div class='qc-var-attrs'>{attrs_ul}</div>"
        f"<pre class='qc-var-data'>{data_repr}</pre>"
    )


def _mapping_section(mapping, name, details_func, max_items_collapse, enabled=True):
    n_items = len(mapping)
    collapsed = n_items >= max_items_collapse

    return collapsible_section(
        name,
        details=details_func(mapping),
        n_items=n_items,
        enabled=enabled,
        collapsed=collapsed,
    )


coord_section = partial(
    _mapping_section,
    name="Independent parameters",
    details_func=summarize_coords,
    max_items_collapse=25,
)

datavar_section = partial(
    _mapping_section,
    name="Dependent parameters",
    details_func=summarize_vars,
    max_items_collapse=15,
)


def dataset_repr(qc_ds):
    ds = _qc_ds_info(qc_ds)
    obj_type = "qcodes.{}".format(type(qc_ds).__name__)
    header_components = [f"<div class='qc-obj-type'>{escape(obj_type)}</div>"]

    sections = [
        dim_section(ds["dims"]),
        coord_section(ds["coords"]),
        datavar_section(ds["variables"]),
        # attr_section(ds.attrs),  # XXX: add extra info
    ]

    return _obj_repr(header_components, sections)


def _qc_ds_info(qc_ds):
    dfs = qc_ds.get_data_as_pandas_dataframe()
    df = pd.concat(dfs.values(), axis=1)

    dims = {level.name: level.values for level in df.index.levels}
    variables_values = {k: df[k].values for k in df.keys()}

    attrs_mapping = {}
    for p, spec in qc_ds.paramspecs.items():
        attrs = {
            "unit": spec.unit,
            "label": spec.label,
            "type": spec.type,
        }

        vals = dims[p] if not spec.depends_on else variables_values[p]

        depends_on = spec.depends_on.split(", ")
        attrs["depends_on"] = depends_on if depends_on != [""] else []
        attrs["min"] = vals.min()
        attrs["max"] = vals.max()
        attrs["npoints"] = len(vals)
        if len(vals) > 1:
            attrs["Δx"] = vals[1] - vals[0]

        attrs_mapping[p] = attrs

    coords = {k: dict(attrs=attrs_mapping[k], array=dims[k]) for k in dims}
    variables = {
        k: dict(attrs=attrs_mapping[k], array=variables_values[k])
        for k in variables_values
    }
    ds = dict(dims=dims, coords=coords, variables=variables)
    return ds


def _repr_html_(qc_ds):
    from IPython.display import HTML

    return HTML(dataset_repr(qc_ds))
