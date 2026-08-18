import pandas as pd
from sklearn.metrics import confusion_matrix


VALID_CLASSES = list(range(9))


CLASS_NAMES = {
    0: "Water",
    1: "Trees",
    2: "Grass",
    3: "Flooded vegetation",
    4: "Crops",
    5: "Shrub & scrub",
    6: "Built-up",
    7: "Bare ground",
    8: "Snow & ice",
}


def create_confusion_matrix(reference, predicted):
    """
    Create a LULC confusion matrix.

    Rows    = Reference / Ground Truth
    Columns = Predicted / Dynamic World
    """

    matrix = confusion_matrix(
        reference,
        predicted,
        labels=VALID_CLASSES
    )

    names = [
        CLASS_NAMES[class_id]
        for class_id in VALID_CLASSES
    ]

    return pd.DataFrame(
        matrix,
        index=names,
        columns=names
    )


def save_confusion_matrix(matrix, output_path):
    """
    Save confusion matrix as CSV.
    """

    matrix.to_csv(output_path)