"""FAULTLINE Day 14: verified intervals + paired statistical design.

Dependency-free statistical utilities so every comparison in the project can carry
uncertainty and be tested honestly. Builds conceptually on Days 3/7 (Wilson) and
consumes Day 13's dataset in the grounded experiment.

Public surface:
    mathfns:   norm_cdf, norm_ppf, chi2_sf_df1, binom_pmf, binom_two_sided_p
    intervals: wilson_interval, bootstrap_ci
    paired:    paired_table, mcnemar_test, mcnemar_from_pairs, PairedTable
    verify:    verify_all
    interpret: interpret_interval, interpret_mcnemar
    experiment: build_report
"""
from . import experiment, interpret, intervals, mathfns, paired, verify
from .experiment import build_report
from .interpret import interpret_interval, interpret_mcnemar
from .intervals import bootstrap_ci, wilson_interval
from .mathfns import binom_pmf, binom_two_sided_p, chi2_sf_df1, norm_cdf, norm_ppf
from .paired import PairedTable, mcnemar_from_pairs, mcnemar_test, paired_table
from .verify import verify_all

__all__ = [
    "norm_cdf", "norm_ppf", "chi2_sf_df1", "binom_pmf", "binom_two_sided_p",
    "wilson_interval", "bootstrap_ci",
    "paired_table", "mcnemar_test", "mcnemar_from_pairs", "PairedTable",
    "verify_all", "interpret_interval", "interpret_mcnemar", "build_report",
    "mathfns", "intervals", "paired", "verify", "interpret", "experiment",
]
