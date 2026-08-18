from pathlib import Path

import pandas as pd

from .confusion_matrix import create_confusion_matrix
from .metrics import calculate_metrics


# Your 9 valid Dynamic World / LULC classes
VALID_CLASSES = set(range(9))

# Special values
UNLABELLED_CLASS = -1
NODATA_CLASS = 255


# Exact columns required from your validation CSV
REQUIRED_COLUMNS = {
    "Latitude",
    "Longitude",
    "Point_ID",
    "Reference_Class",
    "DW_Class",
    "Year",
}


def load_validation_points(csv_path):
    """
    Load validation points from a CSV file.
    """

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
    """
    Prepare the CSV for accuracy assessment.

    Removes:
    - Reference_Class = -1 (not labelled)
    - Reference_Class outside 0-8
    - DW_Class outside 0-8
    - missing/non-numeric class values
    """

    data = df.copy()

    # Convert class columns to numbers
    data["Reference_Class"] = pd.to_numeric(
        data["Reference_Class"],
        errors="coerce"
    )

    data["DW_Class"] = pd.to_numeric(
        data["DW_Class"],
        errors="coerce"
    )

    # Keep only valid reference classes 0-8
    data = data[
        data["Reference_Class"].isin(VALID_CLASSES)
    ]

    # Keep only valid predicted classes 0-8
    data = data[
        data["DW_Class"].isin(VALID_CLASSES)
    ]

    data = data.copy()

    data["Reference_Class"] = data[
        "Reference_Class"
    ].astype(int)

    data["DW_Class"] = data[
        "DW_Class"
    ].astype(int)

    return data


def validate_dataframe(df):
    """
    Perform the complete validation process.

    Returns:
        validation_table
        confusion_matrix
        metrics
    """

    prepared_data = prepare_validation_data(df)

    if prepared_data.empty:
        raise ValueError(
            "No labelled validation points are available.\n\n"
            "Reference_Class must contain values from 0 to 8.\n"
            "Currently your unlabelled points have Reference_Class = -1."
        )

    reference = prepared_data[
        "Reference_Class"
    ].to_numpy()

    predicted = prepared_data[
        "DW_Class"
    ].to_numpy()

    # Create confusion matrix
    matrix = create_confusion_matrix(
        reference,
        predicted
    )

    # Calculate accuracy metrics
    metrics = calculate_metrics(
        reference,
        predicted
    )

    return prepared_data, matrix, metrics


def validate_csv(csv_path, output_directory=None):
    """
    Run validation directly from a CSV.

    Parameters
    ----------
    csv_path : str or Path
        Path to validation CSV.

    output_directory : str or Path, optional
        Folder where validation results will be saved.

    Returns
    -------
    dict
        Validation table, confusion matrix and metrics.
    """

    # Load CSV
    df = load_validation_points(csv_path)

    # Run validation
    validation_table, matrix, metrics = validate_dataframe(df)

    # Save results if an output directory is provided
    if output_directory is not None:

        output_directory = Path(output_directory)

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # Point-by-point validation table
        validation_table.to_csv(
            output_directory / "validation_results.csv",
            index=False
        )

        # Confusion matrix
        matrix.to_csv(
            output_directory / "confusion_matrix.csv"
        )

        # Overall accuracy summary
        summary = {
            "Year": int(
                validation_table["Year"].iloc[0]
            ),
            "Validation_Points": len(
                validation_table
            ),
            "Overall_Accuracy": metrics[
                "overall_accuracy"
            ],
            "Kappa": metrics["kappa"],
        }

        pd.DataFrame([summary]).to_csv(
            output_directory / "accuracy_summary.csv",
            index=False
        )

    return {
        "validation_table": validation_table,
        "confusion_matrix": matrix,
        "metrics": metrics,
    }