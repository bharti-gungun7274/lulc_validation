import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    cohen_kappa_score,
    classification_report
)


# ============================================================
# SETTINGS
# ============================================================

YEARS = [2018, 2020, 2022, 2024]

BASE_DIR = "data"
OUTPUT_DIR = "output"

# ------------------------------------------------------------
# IMPORTANT:
# Change these if your CSV uses different column names.
# ------------------------------------------------------------

LAT_COLUMN = "Latitude"
LON_COLUMN = "Longitude"

# If your CSV has an ID column:
ID_COLUMN = "Point_ID"


# ============================================================
# GET FILE PATHS FOR A YEAR
# ============================================================

def get_year_files(year):

    year_dir = os.path.join(
        BASE_DIR,
        str(year)
    )

    dw_raster = os.path.join(
        year_dir,
        f"dw_{year}.tif"
    )

    reference_raster = os.path.join(
        year_dir,
        f"reference_{year}.tif"
    )

    validation_csv = os.path.join(
        year_dir,
        f"validation_points_{year}.csv"
    )

    return (
        dw_raster,
        reference_raster,
        validation_csv
    )


# ============================================================
# CHECK FILES
# ============================================================

def check_files(
    dw_raster,
    reference_raster,
    validation_csv
):

    files = {
        "Dynamic World raster": dw_raster,
        "Reference raster": reference_raster,
        "Validation CSV": validation_csv
    }

    for name, path in files.items():

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"\n{name} not found:\n{path}"
            )


# ============================================================
# LOAD VALIDATION CSV
# ============================================================

def load_validation_points(csv_path):

    print(
        f"\nLoading validation points:\n{csv_path}"
    )

    df = pd.read_csv(csv_path)

    print(
        "Columns:",
        df.columns.tolist()
    )

    print(
        "Number of points:",
        len(df)
    )

    # --------------------------------------------------------
    # Check coordinate columns
    # --------------------------------------------------------

    if LAT_COLUMN not in df.columns:

        raise ValueError(
            f"\nLatitude column '{LAT_COLUMN}' "
            f"not found in CSV.\n"
            f"Available columns: "
            f"{df.columns.tolist()}"
        )

    if LON_COLUMN not in df.columns:

        raise ValueError(
            f"\nLongitude column '{LON_COLUMN}' "
            f"not found in CSV.\n"
            f"Available columns: "
            f"{df.columns.tolist()}"
        )

    # --------------------------------------------------------
    # Create GeoDataFrame
    # --------------------------------------------------------

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df[LON_COLUMN],
            df[LAT_COLUMN]
        ),
        crs="EPSG:4326"
    )

    return points


# ============================================================
# PRINT RASTER INFORMATION
# ============================================================

def print_raster_info(
    raster_path,
    name
):

    with rasterio.open(raster_path) as src:

        print("\n" + "-" * 60)
        print(name)
        print("-" * 60)

        print("CRS:", src.crs)
        print("Width:", src.width)
        print("Height:", src.height)
        print("Resolution:", src.res)
        print("Bands:", src.count)
        print("Data type:", src.dtypes[0])
        print("NoData:", src.nodata)
        print("Bounds:", src.bounds)


# ============================================================
# REPROJECT POINTS
# ============================================================

def reproject_points(
    points,
    raster_path
):

    with rasterio.open(raster_path) as src:

        raster_crs = src.crs

    if points.crs != raster_crs:

        print(
            "\nReprojecting validation points..."
        )

        points = points.to_crs(
            raster_crs
        )

    return points


# ============================================================
# EXTRACT RASTER VALUE
# ============================================================

def extract_raster_values(
    points,
    raster_path,
    column_name
):

    values = []

    with rasterio.open(raster_path) as src:

        raster = src.read(1)

        for point in points.geometry:

            # ------------------------------------------------
            # Check whether point is inside raster
            # ------------------------------------------------

            if not (
                src.bounds.left <= point.x <= src.bounds.right
                and
                src.bounds.bottom <= point.y <= src.bounds.top
            ):

                values.append(np.nan)

                continue

            # ------------------------------------------------
            # Convert coordinate to row/column
            # ------------------------------------------------

            row, col = src.index(
                point.x,
                point.y
            )

            # ------------------------------------------------
            # Safety check
            # ------------------------------------------------

            if (
                row < 0
                or row >= src.height
                or col < 0
                or col >= src.width
            ):

                values.append(np.nan)

                continue

            # ------------------------------------------------
            # Extract value
            # ------------------------------------------------

            value = raster[row, col]

            # ------------------------------------------------
            # Check NoData
            # ------------------------------------------------

            if src.nodata is not None:

                if value == src.nodata:

                    values.append(np.nan)

                    continue

            values.append(value)

    points[column_name] = values

    return points


# ============================================================
# VALIDATE ONE YEAR
# ============================================================

def validate_year(year):

    print("\n")
    print("=" * 70)
    print(f"STARTING VALIDATION FOR {year}")
    print("=" * 70)

    # --------------------------------------------------------
    # Get files
    # --------------------------------------------------------

    (
        dw_raster,
        reference_raster,
        validation_csv
    ) = get_year_files(year)

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    check_files(
        dw_raster,
        reference_raster,
        validation_csv
    )

    # --------------------------------------------------------
    # Print raster information
    # --------------------------------------------------------

    print_raster_info(
        dw_raster,
        "DYNAMIC WORLD RASTER"
    )

    print_raster_info(
        reference_raster,
        "REFERENCE RASTER"
    )

    # --------------------------------------------------------
    # Load validation points
    # --------------------------------------------------------

    points = load_validation_points(
        validation_csv
    )

    # --------------------------------------------------------
    # Reproject points to DW CRS
    # --------------------------------------------------------

    points = reproject_points(
        points,
        dw_raster
    )

    # --------------------------------------------------------
    # Extract Dynamic World classes
    # --------------------------------------------------------

    print(
        "\nExtracting Dynamic World classes..."
    )

    points = extract_raster_values(
        points,
        dw_raster,
        "dw_class"
    )

    # --------------------------------------------------------
    # Extract Reference classes
    # --------------------------------------------------------

    print(
        "Extracting reference classes..."
    )

    points = extract_raster_values(
        points,
        reference_raster,
        "reference_class"
    )

    # --------------------------------------------------------
    # Report missing values
    # --------------------------------------------------------

    print(
        "\nMissing DW values:",
        points["dw_class"].isna().sum()
    )

    print(
        "Missing reference values:",
        points["reference_class"].isna().sum()
    )

    # --------------------------------------------------------
    # Remove invalid points
    # --------------------------------------------------------

    valid = points.dropna(
        subset=[
            "dw_class",
            "reference_class"
        ]
    ).copy()

    print(
        "\nTotal points:",
        len(points)
    )

    print(
        "Valid points:",
        len(valid)
    )

    # --------------------------------------------------------
    # Convert class values to integers
    # --------------------------------------------------------

    valid["dw_class"] = (
        valid["dw_class"].astype(int)
    )

    valid["reference_class"] = (
        valid["reference_class"].astype(int)
    )

    # --------------------------------------------------------
    # Compare classes
    # --------------------------------------------------------

    valid["correct"] = (
        valid["dw_class"]
        ==
        valid["reference_class"]
    )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    y_true = valid["reference_class"]
    y_pred = valid["dw_class"]

    overall_accuracy = accuracy_score(
        y_true,
        y_pred
    )

    # --------------------------------------------------------
    # Kappa
    # --------------------------------------------------------

    kappa = cohen_kappa_score(
        y_true,
        y_pred
    )

    # --------------------------------------------------------
    # Class labels
    # --------------------------------------------------------

    labels = sorted(
        set(y_true) | set(y_pred)
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=labels
    )

    cm_df = pd.DataFrame(
        cm,
        index=[
            f"Reference_{x}"
            for x in labels
        ],
        columns=[
            f"DW_{x}"
            for x in labels
        ]
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0
    )

    report_df = pd.DataFrame(
        report
    ).transpose()

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print("\n")
    print("=" * 70)
    print(f"RESULTS FOR {year}")
    print("=" * 70)

    print(
        f"\nOverall Accuracy: "
        f"{overall_accuracy * 100:.2f}%"
    )

    print(
        f"Kappa: "
        f"{kappa:.4f}"
    )

    print("\nConfusion Matrix:")
    print(cm_df)

    print("\nClassification Report:")
    print(report_df)

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    year_output = os.path.join(
        OUTPUT_DIR,
        str(year)
    )

    os.makedirs(
        year_output,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Point-level results
    # --------------------------------------------------------

    result_file = os.path.join(
        year_output,
        f"validation_results_{year}.csv"
    )

    valid.drop(
        columns="geometry"
    ).to_csv(
        result_file,
        index=False
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    cm_file = os.path.join(
        year_output,
        f"confusion_matrix_{year}.csv"
    )

    cm_df.to_csv(
        cm_file
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    report_file = os.path.join(
        year_output,
        f"classification_report_{year}.csv"
    )

    report_df.to_csv(
        report_file
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    correct_points = int(
        valid["correct"].sum()
    )

    summary = pd.DataFrame({

        "Year": [year],

        "Total_Points": [
            len(points)
        ],

        "Valid_Points": [
            len(valid)
        ],

        "Correct_Points": [
            correct_points
        ],

        "Overall_Accuracy": [
            overall_accuracy
        ],

        "Kappa": [
            kappa
        ]

    })

    summary_file = os.path.join(
        year_output,
        f"accuracy_summary_{year}.csv"
    )

    summary.to_csv(
        summary_file,
        index=False
    )

    print("\nOutput files:")

    print(result_file)
    print(cm_file)
    print(report_file)
    print(summary_file)

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("MULTI-YEAR LULC VALIDATION")
    print("=" * 70)

    all_results = []

    # --------------------------------------------------------
    # Run every year
    # --------------------------------------------------------

    for year in YEARS:

        try:

            summary = validate_year(
                year
            )

            all_results.append(
                summary
            )

        except Exception as error:

            print("\n")
            print("=" * 70)
            print(f"ERROR IN YEAR {year}")
            print("=" * 70)

            print(error)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    if len(all_results) > 0:

        final_summary = pd.concat(
            all_results,
            ignore_index=True
        )

        os.makedirs(
            OUTPUT_DIR,
            exist_ok=True
        )

        final_file = os.path.join(
            OUTPUT_DIR,
            "multi_year_accuracy_summary.csv"
        )

        final_summary.to_csv(
            final_file,
            index=False
        )

        print("\n")
        print("=" * 70)
        print("FINAL MULTI-YEAR SUMMARY")
        print("=" * 70)

        print(
            final_summary.to_string(
                index=False
            )
        )

        print(
            "\nFinal summary saved to:"
        )

        print(final_file)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()