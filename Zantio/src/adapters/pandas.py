import pandas as pd

from dataclasses import is_dataclass, fields
from typing import Any

from RESTclients.CloudFactory import cloudfactory as cf


def flatten_dataclass(obj, parent_key: str = "", sep: str = "_") -> dict:
    flat_dict = {}

    if not is_dataclass(obj):
        return obj

    for f in fields(obj):
        value = getattr(obj, f.name)
        key = f"{parent_key}{sep}{f.name}" if parent_key else f.name

        # Nested dataclass
        if is_dataclass(value):
            flat_dict.update(flatten_dataclass(value, key, sep))

        # List of dataclasses or primitives
        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_key = f"{key}{sep}{i}"
                if is_dataclass(item):
                    flat_dict.update(flatten_dataclass(item, item_key, sep))
                else:
                    flat_dict[item_key] = item

        # Dict of primitives
        elif isinstance(value, dict):
            for k, v in value.items():
                flat_dict[f"{key}{sep}{k}"] = v

        else:
            flat_dict[key] = value

    return flat_dict

def dataclasses_to_df(objs: list[Any]) -> pd.DataFrame:
    flat = [flatten_dataclass(obj) for obj in objs]
    return pd.DataFrame(flat)


def main(cloudfac_client: cf.CloudFactoryClient):
    invoices = cloudfac_client.fetch_latest_invoices()

    if not invoices:
        return

    inv_df = dataclasses_to_df(invoices)

    print(inv_df)

    if "postingDate" not in inv_df.columns:
        print("⚠ 'postingDate' not present on invoices; cannot filter by month.")
        return