"""faultline_p2.stats package.

Exports:
- wilson, wilson_interval
- mcnemar, paired_table, mcnemar_from_pairs
- bootstrap, bootstrap_ci
- pass_hat_k, naive_p_k
"""
from faultline_p2.stats.intervals import bootstrap, bootstrap_ci, wilson, wilson_interval
from faultline_p2.stats.paired import (
    PairedTable,
    mcnemar,
    mcnemar_from_pairs,
    paired_table,
)
from faultline_p2.stats.passk import naive_p_k, pass_hat_k

__all__ = [
    "wilson",
    "wilson_interval",
    "mcnemar",
    "paired_table",
    "mcnemar_from_pairs",
    "PairedTable",
    "bootstrap",
    "bootstrap_ci",
    "pass_hat_k",
    "naive_p_k",
]
