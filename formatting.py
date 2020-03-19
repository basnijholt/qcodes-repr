"""String formatting routines for qcodes.DataSet.__repr__.

This code heavily borrows from `xarray`, whose license can be found
in `licenses/XARRAY_LICENSE`.
"""

import contextlib
from datetime import datetime, timedelta
from itertools import zip_longest

import numpy as np
import pandas as pd
from pandas.errors import OutOfBoundsDatetime

from xarray.core.options import OPTIONS


def _get_indexer_at_least_n_items(shape, n_desired, from_end):
    assert 0 < n_desired <= np.prod(shape)
    cum_items = np.cumprod(shape[::-1])
    n_steps = np.argmax(cum_items >= n_desired)
    stop = int(np.ceil(float(n_desired) / np.r_[1, cum_items][n_steps]))
    indexer = (
        ((-1 if from_end else 0),) * (len(shape) - 1 - n_steps)
        + ((slice(-stop, None) if from_end else slice(stop)),)
        + (slice(None),) * n_steps
    )
    return indexer


def first_n_items(array, n_desired):
    """Returns the first n_desired items of an array"""
    # Unfortunately, we can't just do array.flat[:n_desired] here because it
    # might not be a numpy.ndarray. Moreover, access to elements of the array
    # could be very expensive (e.g. if it's only available over DAP), so go out
    # of our way to get them in a single call to __getitem__ using only slices.
    if n_desired < 1:
        raise ValueError("must request at least one item")

    if array.size == 0:
        # work around for https://github.com/numpy/numpy/issues/5195
        return []

    if n_desired < array.size:
        indexer = _get_indexer_at_least_n_items(array.shape, n_desired, from_end=False)
        array = array[indexer]
    return np.asarray(array).flat[:n_desired]


def last_n_items(array, n_desired):
    """Returns the last n_desired items of an array"""
    # Unfortunately, we can't just do array.flat[-n_desired:] here because it
    # might not be a numpy.ndarray. Moreover, access to elements of the array
    # could be very expensive (e.g. if it's only available over DAP), so go out
    # of our way to get them in a single call to __getitem__ using only slices.
    if (n_desired == 0) or (array.size == 0):
        return []

    if n_desired < array.size:
        indexer = _get_indexer_at_least_n_items(array.shape, n_desired, from_end=True)
        array = array[indexer]
    return np.asarray(array).flat[-n_desired:]


# def last_item(array):
#     """Returns the last item of an array in a list or an empty list."""
#     if array.size == 0:
#         # work around for https://github.com/numpy/numpy/issues/5195
#         return []

#     indexer = (slice(-1, None),) * array.ndim
#     return np.ravel(np.asarray(array[indexer])).tolist()


def format_timestamp(t):
    """Cast given object to a Timestamp and return a nicely formatted string"""
    # Timestamp is only valid for 1678 to 2262
    try:
        datetime_str = str(pd.Timestamp(t))
    except OutOfBoundsDatetime:
        datetime_str = str(t)

    try:
        date_str, time_str = datetime_str.split()
    except ValueError:
        # catch NaT and others that don't split nicely
        return datetime_str
    else:
        if time_str == "00:00:00":
            return date_str
        else:
            return f"{date_str}T{time_str}"


def format_timedelta(t, timedelta_format=None):
    """Cast given object to a Timestamp and return a nicely formatted string"""
    timedelta_str = str(pd.Timedelta(t))
    try:
        days_str, time_str = timedelta_str.split(" days ")
    except ValueError:
        # catch NaT and others that don't split nicely
        return timedelta_str
    else:
        if timedelta_format == "date":
            return days_str + " days"
        elif timedelta_format == "time":
            return time_str
        else:
            return timedelta_str


def format_item(x, timedelta_format=None, quote_strings=True):
    """Returns a succinct summary of an object as a string"""
    if isinstance(x, (np.datetime64, datetime)):
        return format_timestamp(x)
    if isinstance(x, (np.timedelta64, timedelta)):
        return format_timedelta(x, timedelta_format=timedelta_format)
    elif isinstance(x, (str, bytes)):
        return repr(x) if quote_strings else x
    elif isinstance(x, (float, np.float)):
        return f"{x:.4}"
    else:
        return str(x)


def format_items(x):
    """Returns a succinct summaries of all items in a sequence as strings"""
    x = np.asarray(x)
    timedelta_format = "datetime"
    if np.issubdtype(x.dtype, np.timedelta64):
        x = np.asarray(x, dtype="timedelta64[ns]")
        day_part = x[~pd.isnull(x)].astype("timedelta64[D]").astype("timedelta64[ns]")
        time_needed = x[~pd.isnull(x)] != day_part
        day_needed = day_part != np.timedelta64(0, "ns")
        if np.logical_not(day_needed).all():
            timedelta_format = "time"
        elif np.logical_not(time_needed).all():
            timedelta_format = "date"

    formatted = [format_item(xi, timedelta_format) for xi in x]
    return formatted


def format_array_flat(array, max_width):
    """Return a formatted string for as many items in the flattened version of
    array that will fit within max_width characters.
    """
    # every item will take up at least two characters, but we always want to
    # print at least first and last items
    max_possibly_relevant = min(
        max(array.size, 1), max(int(np.ceil(max_width / 2.0)), 2)
    )
    relevant_front_items = format_items(
        first_n_items(array, (max_possibly_relevant + 1) // 2)
    )
    relevant_back_items = format_items(last_n_items(array, max_possibly_relevant // 2))
    # interleave relevant front and back items:
    #     [a, b, c] and [y, z] -> [a, z, b, y, c]
    relevant_items = sum(
        zip_longest(relevant_front_items, reversed(relevant_back_items)), ()
    )[:max_possibly_relevant]

    cum_len = np.cumsum([len(s) + 1 for s in relevant_items]) - 1
    if (array.size > 2) and (
        (max_possibly_relevant < array.size) or (cum_len > max_width).any()
    ):
        padding = " ... "
        count = min(
            array.size, max(np.argmax(cum_len + len(padding) - 1 > max_width), 2)
        )
    else:
        count = array.size
        padding = "" if (count <= 1) else " "

    num_front = (count + 1) // 2
    num_back = count - num_front
    # note that num_back is 0 <--> array.size is 0 or 1
    #                         <--> relevant_back_items is []
    pprint_str = (
        " ".join(relevant_front_items[:num_front])
        + padding
        + " ".join(relevant_back_items[-num_back:])
    )
    return pprint_str


@contextlib.contextmanager
def set_numpy_options(*args, **kwargs):
    original = np.get_printoptions()
    np.set_printoptions(*args, **kwargs)
    try:
        yield
    finally:
        np.set_printoptions(**original)


def short_numpy_repr(array):
    array = np.asarray(array)

    # default to lower precision so a full (abbreviated) line can fit on
    # one line with the default display_width
    options = {"precision": 6, "linewidth": OPTIONS["display_width"], "threshold": 200}
    if array.ndim < 3:
        edgeitems = 3
    elif array.ndim == 3:
        edgeitems = 2
    else:
        edgeitems = 1
    options["edgeitems"] = edgeitems
    with set_numpy_options(**options):
        return repr(array)


def short_data_repr(array):
    """Format "data" for DataArray and Variable."""
    if isinstance(array, np.ndarray):
        return short_numpy_repr(array)
    elif array._in_memory or array.size < 1e5:
        return short_numpy_repr(array)
    else:
        # internal xarray array type
        return f"[{array.size} values with dtype={array.dtype}]"
