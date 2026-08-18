from pathlib import Path

import pandas as pd

from .confusion_matrix import create_confusion_matrix
from .metrics import calculate_metrics


VALID_CLASSES = set(range(9))

UNLABELLED_CLASS = -1
NODATA_CLASS = 255


REQUIRED_COLUMNS = {
    "Latitude",
    "Longitude",
    "Point_ID",
    "Reference_Class",
    "DW_Class",
    "Year",
}


def load_validation_points(csv_path):

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Validation CSV not found:\n{csv_path}"
        )

    df = pd.read_csv(csv_path)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            "The following required columns are missing:\n"
            f"{sorted(missing_columns)}"
        )

    return df


def prepare_validation_data(df):

    data = df.copy()

    data["Reference_Class"] = pd.to_numeric(
        data["Reference_Class"],
        errors="coerce",
    )

    data["DW_Class"] = pd.to_numeric(
        data["DW_Class"],
        errors="coerce",
    )

    data = data[
        data["Reference_Class"].isin(
            VALID_CLASSES
        )
    ]

    data = data[
        data["DW_Class"].isin(
            VALID_CLASSES
        )
    ]

    data = data.copy()

    data["Reference_Class"] = (
        data["Reference_Class"].astype(int)
    )

    data["DW_Class"] = (
        data["DW_Class"].astype(int)
    )

    return data


def validate_dataframe(df):

    prepared_data = prepare_validation_data(df)

    if prepared_data.empty:
        raise ValueError(
            "No valid labelled validation points "
            "are available."
        )

    reference = prepared_data[
        "Reference_Class"
    ].to_numpy()

    predicted = prepared_data[
        "DW_Class"
    ].to_numpy()

    matrix = create_confusion_matrix(
        reference,
        predicted,
    )

    metrics = calculate_metrics(
        reference,
        predicted,
    )

    return (
        prepared_data,
        matrix,
        metrics,
    )


def validate_csv(
    csv_path,
    output_directory=None,
):

    df = load_validation_points(csv_path)

    validation_table, matrix, metrics = (
        validate_dataframe(df)
    )

    if output_directory is not None:

        output_directory = Path(
            output_directory
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        validation_table.to_csv(
            output_directory
            / "validation_results.csv",
            index=False,
        )

        matrix.to_csv(
            output_directory
            / "confusion_matrix.csv"
        )

        summary = {
            "Year": int(
                validation_table[
                    "Year"
                ].iloc[0]
            ),
            "Validation_Points": len(
                validation_table
            ),
            "Overall_Accuracy": metrics[
                "overall_accuracy"
            ],
            "Kappa": metrics["kappa"],
        }

        pd.DataFrame(
            [summary]
        ).to_csv(
            output_directory
            / "accuracy_summary.csv",
            index=False,
        )

    return {
        "validation_table": validation_table,
        "confusion_matrix": matrix,
        "metrics": metrics,
    }