"""CSV export support."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd


class CsvExporter:
    """Exports generated transaction datasets to CSV."""

    def export(self, dataframe: pd.DataFrame, path: Union[str, Path]) -> Path:
        """Write the dataframe to disk and return the final path."""
        output_path = Path(path)
        dataframe.to_csv(output_path, index=False)
        return output_path
