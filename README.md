# qcodes-repr
View your qcodes database experiments at a glance

Use it in a Jupyter notebook environment like
```python
from formatting_html import _repr_html_
from qcodes.dataset import initialise_or_create_database_at

initialise_or_create_database_at("phase_2_run_1.db")
qc_ds = qcodes.experiments()[0].data_sets()
_repr_html_(qc_ds)
```
