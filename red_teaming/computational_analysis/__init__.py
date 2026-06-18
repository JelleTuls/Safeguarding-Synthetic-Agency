"""Reproducible computational analysis for SSA red-team result reports."""

from .pipeline import ANALYSIS_ARTIFACTS
from .pipeline import analysis_artifact_path
from .pipeline import analysis_output_dir
from .pipeline import generate_analysis

__all__ = [
    "ANALYSIS_ARTIFACTS",
    "analysis_artifact_path",
    "analysis_output_dir",
    "generate_analysis",
]
