from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT.parent / "02_Datasets"
CLEAN_DATASET_DIR = DATASET_DIR / "clean"
MODEL_READY_DATASET_DIR = DATASET_DIR / "model_ready"

THERMAL_INPUT = CLEAN_DATASET_DIR / "thermal_comfort_clean_dataset.xlsx"
IEQ_INPUT = CLEAN_DATASET_DIR / "ieq_clean_dataset.xlsx"
THERMAL_OUTPUT = MODEL_READY_DATASET_DIR / "thermal_comfort_model_dataset.xlsx"
IEQ_OUTPUT = MODEL_READY_DATASET_DIR / "ieq_model_dataset.xlsx"

RANDOM_SEED = 20260505

COMMON_METADATA_COLUMNS = ["source_row_number", "TimeVote", "Occupant ID", "Group", "Subgroup", "Student"]
LOCATION_COLUMNS = ["LocationBack", "LocationFront", "LocationLeft", "LocationRight", "LocationMiddle"]
MODEL_DATA_DROP_COLUMNS = ["source_row_number", "Occupant ID", "Group", "Subgroup"]
IEQ_MODEL_DATA_DROP_COLUMNS = ["IEQ satisfaction"]
OUTPUT_METADATA_COLUMNS: list[str] = []

THERMAL_COLUMNS = [
    "Thermal satisfaction",
    "Thermal satisfaction 3-class",
    "Temperature",
    "RH",
    "CLO",
    "Age",
    "Gender",
    "EA",
    *LOCATION_COLUMNS,
    "Ttrend",
    "Vote hour",
    "Vote weekday",
    "Moment",
    "AC on/off",
]

IEQ_COLUMNS = [
    "IEQ satisfaction",
    "IEQ satisfaction 3-class",
    "Temperature",
    "RH",
    "CLO",
    "CO2",
    "Lighting",
    "Sound",
    "Age",
    "Gender",
    "EA",
    *LOCATION_COLUMNS,
    "Ttrend",
    "Vote hour",
    "Vote weekday",
    "Moment",
    "AC on/off",
]


def is_imputation_metadata_column(column: str) -> bool:
    return column.startswith(("Imputed ", "Derived ", "Estimated "))


def enforce_location_boolean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in LOCATION_COLUMNS:
        if column in result.columns:
            result[column] = result[column].astype("boolean")
    return result


def groupwise_numeric_impute(
    frame: pd.DataFrame,
    column: str,
    groupings: tuple[tuple[str, ...], ...],
) -> tuple[pd.Series, pd.Series]:
    result = frame[column].copy()
    missing_original = result.isna()

    for grouping in groupings:
        still_missing = result.isna()
        if not still_missing.any():
            break
        fill_values = frame.groupby(list(grouping), dropna=False)[column].transform("median")
        use_fill = still_missing & fill_values.notna()
        result.loc[use_fill] = fill_values.loc[use_fill]

    still_missing = result.isna()
    if still_missing.any():
        result.loc[still_missing] = frame[column].median()

    return result, missing_original


def impute_age(frame: pd.DataFrame) -> tuple[pd.Series, dict[str, pd.Series]]:
    original = frame["Age"].copy()
    result = original.copy()
    missing_original = result.isna()

    known_age_by_occupant = (
        frame.loc[original.notna() & frame["Occupant ID"].notna()]
        .groupby("Occupant ID")["Age"]
        .median()
    )
    derived_values = frame["Occupant ID"].map(known_age_by_occupant)
    derived_from_id = missing_original & derived_values.notna()
    result.loc[derived_from_id] = derived_values.loc[derived_from_id]

    for grouping in (("Group", "Student"), ("Group",)):
        still_missing = result.isna()
        if not still_missing.any():
            break
        fill_values = frame.groupby(list(grouping), dropna=False)["Age"].transform("median")
        use_fill = still_missing & fill_values.notna()
        result.loc[use_fill] = fill_values.loc[use_fill]

    still_missing = result.isna()
    if still_missing.any():
        result.loc[still_missing] = frame["Age"].median()

    estimated = missing_original & ~derived_from_id
    return result, {
        "Derived Age from ID": derived_from_id,
        "Estimated Age": estimated,
    }


def impute_gender(frame: pd.DataFrame) -> tuple[pd.Series, dict[str, pd.Series]]:
    original = frame["Gender"].copy()
    result = original.copy()
    missing_original = original.isna()

    known_gender_by_occupant = (
        frame.loc[original.notna() & frame["Occupant ID"].notna()]
        .groupby("Occupant ID")["Gender"]
        .agg(lambda values: values.dropna().iloc[0])
    )
    inferred = frame["Occupant ID"].map(known_gender_by_occupant)
    derived_from_id = missing_original & inferred.notna()
    result.loc[derived_from_id] = inferred.loc[derived_from_id]

    rng = np.random.default_rng(RANDOM_SEED)
    known = frame.loc[original.notna(), ["Group", "Gender"]].copy()
    group_distributions = {
        group: counts / counts.sum()
        for group, counts in known.groupby("Group")["Gender"].value_counts().unstack(fill_value=0).iterrows()
        if counts.sum() > 0
    }
    overall_counts = known["Gender"].value_counts()
    overall_distribution = overall_counts / overall_counts.sum()

    random_assignments = {}
    for occupant_id in sorted(frame.loc[result.isna(), "Occupant ID"].dropna().unique()):
        group = frame.loc[frame["Occupant ID"] == occupant_id, "Group"].dropna()
        distribution = group_distributions.get(group.iloc[0], overall_distribution) if not group.empty else overall_distribution
        labels = distribution.index.to_numpy()
        probabilities = distribution.to_numpy(dtype=float)
        random_assignments[occupant_id] = rng.choice(labels, p=probabilities / probabilities.sum())

    random_values = frame["Occupant ID"].map(random_assignments)
    use_random = result.isna() & random_values.notna()
    result.loc[use_random] = random_values.loc[use_random]

    still_missing = result.isna()
    if still_missing.any():
        for row_index in result.loc[still_missing].index:
            group = frame.at[row_index, "Group"]
            distribution = group_distributions.get(group, overall_distribution)
            labels = distribution.index.to_numpy()
            probabilities = distribution.to_numpy(dtype=float)
            result.at[row_index] = rng.choice(labels, p=probabilities / probabilities.sum())

    estimated = missing_original & ~derived_from_id
    return result, {
        "Derived Gender from ID": derived_from_id,
        "Estimated Gender": estimated,
    }


def impute_missing_location_as_middle(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    result = frame.copy()
    missing_location = result[LOCATION_COLUMNS].isna().any(axis=1)
    for column in LOCATION_COLUMNS:
        result.loc[missing_location, column] = False
        result[column] = result[column].astype("boolean")
    result.loc[missing_location, "LocationMiddle"] = True
    return result, missing_location


def apply_imputation(data: pd.DataFrame, feature_columns: list[str], include_ieq_features: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = data.copy()
    summaries = []
    metadata_flags: dict[str, pd.Series] = {}

    def record(column: str, missing_before: pd.Series, strategy: str) -> None:
        summaries.append(
            {
                "column": column,
                "missing_before": int(missing_before.sum()),
                "missing_after": int(result[column].isna().sum()),
                "strategy": strategy,
            }
        )

    result["CLO"], missing = groupwise_numeric_impute(result, "CLO", (("Group",),))
    record("CLO", missing, "Median imputation within Group, falling back to global median.")

    result["Age"], age_metadata = impute_age(result)
    metadata_flags.update(age_metadata)
    age_missing = age_metadata["Derived Age from ID"] | age_metadata["Estimated Age"]
    record("Age", age_missing, "Transferred from matching Occupant ID when possible; otherwise estimated from Group + Student status, Group, and global medians.")

    result["Gender"], gender_metadata = impute_gender(result)
    metadata_flags.update(gender_metadata)
    gender_missing = gender_metadata["Derived Gender from ID"] | gender_metadata["Estimated Gender"]
    record("Gender", gender_missing, "Transferred from matching Occupant ID when possible; otherwise seeded random draw from Group gender distribution.")

    location_missing_before = {column: result[column].isna() for column in LOCATION_COLUMNS}
    result, estimated_location_middle = impute_missing_location_as_middle(result)
    metadata_flags["Estimated LocationMiddle"] = estimated_location_middle
    for column in LOCATION_COLUMNS:
        record(column, location_missing_before[column], "Missing classroom location defaults to LocationMiddle.")

    result["Ttrend"], missing = groupwise_numeric_impute(result, "Ttrend", (("Group", "Subgroup"), ("Group",)))
    record("Ttrend", missing, "Median imputation within Group + Subgroup, falling back to Group and global medians.")

    if include_ieq_features:
        for column in ("Sound", "Lighting"):
            result[column], missing = groupwise_numeric_impute(result, column, (("Group", "Subgroup"), ("Group",)))
            record(column, missing, "Median imputation within Group + Subgroup, falling back to Group and global medians.")

    ordered_columns = [
        *COMMON_METADATA_COLUMNS,
        *[column for column in result.columns if column not in COMMON_METADATA_COLUMNS],
    ]
    return result[ordered_columns], pd.DataFrame(summaries)


def data_dictionary(columns: Iterable[str], target_name: str) -> pd.DataFrame:
    roles = {column: "input" for column in columns}
    roles[target_name] = "original output"
    for column in columns:
        if column.endswith("3-class"):
            roles[column] = "primary modeling output"
        if is_imputation_metadata_column(column):
            roles[column] = "imputation metadata"
    for column in COMMON_METADATA_COLUMNS:
        roles[column] = "metadata"

    descriptions = {
        "Thermal satisfaction": "Thermal satisfaction vote on the original survey scale.",
        "IEQ satisfaction": "Overall IEQ satisfaction vote on the original survey scale.",
        "Thermal satisfaction 3-class": "Primary modeling target for the thermal comfort paper; Thermal satisfaction collapsed into dissatisfied (1-2), neutral (3), and satisfied (4-5).",
        "IEQ satisfaction 3-class": "Primary modeling target for the IEQ paper; Overall IEQ satisfaction collapsed into dissatisfied (1-2), neutral (3), and satisfied (4-5).",
        "Occupant ID": "Original occupant identifier from ID; retained for personalization and grouped imputation tests.",
        "Group": "Educational case-study group derived from CaseStudy.",
        "Subgroup": "Original subgroup/class label.",
        "Student": "Participant status derived from the Student field.",
        "Temperature": "Room air temperature from Troom.",
        "RH": "Relative humidity.",
        "CLO": "Numeric clothing insulation derived from CLO_Detailed, falling back to CLO_Simple.",
        "CO2": "CO2 concentration.",
        "Lighting": "Lighting measurement.",
        "Sound": "Sound measurement.",
        "Age": "Participant age.",
        "Gender": "Participant gender.",
        "EA": "Outdoor running mean / adaptive comfort context variable from EA.",
        "LocationBack": "Raw classroom location flag from LocationBack.",
        "LocationFront": "Raw classroom location flag from LocationFront.",
        "LocationLeft": "Raw classroom location flag from LocationLeft.",
        "LocationRight": "Raw classroom location flag from LocationRight.",
        "LocationMiddle": "Raw classroom location flag from LocationMiddle.",
        "Ttrend": "Temperature trend feature.",
        "Vote hour": "Hour derived from TimeVote.",
        "Vote weekday": "Weekday name derived from TimeVote.",
        "Moment": "Survey moment/context label.",
        "AC on/off": "Classroom air-conditioning on/off value from AC_Classroom.",
        "source_row_number": "Original row number in FullDataset_CombinedSimple.csv.",
        "TimeVote": "Original timestamp of vote; retained as metadata for traceability.",
        "Estimated Age": "True if Age was missing in the clean dataset and estimated from Group + Student status, Group, or global medians rather than derived from the same Occupant ID.",
    }

    rows = []
    for column in columns:
        if column in descriptions:
            description = descriptions[column]
        elif column.startswith("Imputed "):
            filled_column = column.removeprefix("Imputed ")
            description = f"True if {filled_column} was missing in the clean dataset and filled during model-ready imputation."
        else:
            description = descriptions.get(column, "")
        rows.append(
            {
                "column": column,
                "role": roles.get(column, "input"),
                "description": description,
            }
        )
    return pd.DataFrame(rows)


def model_data_sheet(frame: pd.DataFrame, target_name: str) -> pd.DataFrame:
    drop_columns = [column for column in MODEL_DATA_DROP_COLUMNS if column in frame.columns]
    if target_name == "IEQ satisfaction":
        drop_columns.extend(column for column in IEQ_MODEL_DATA_DROP_COLUMNS if column in frame.columns)
    drop_columns.extend(
        column
        for column in frame.columns
        if is_imputation_metadata_column(column) and column not in OUTPUT_METADATA_COLUMNS
    )
    return frame.drop(columns=drop_columns)


def missingness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = frame.isna().sum().rename("missing_rows").to_frame()
    summary["total_rows"] = len(frame)
    summary["complete_rows"] = summary["total_rows"] - summary["missing_rows"]
    summary["missing_percent"] = (summary["missing_rows"] / len(frame) * 100).round(2)
    summary["complete_percent"] = (summary["complete_rows"] / len(frame) * 100).round(2)
    return summary.reset_index(names="column")


IMPUTATION_PARAGRAPH = (
    "Missing values were imputed using conservative, reproducible rules designed to preserve the ordinal satisfaction targets while avoiding avoidable row loss. "
    "Occupant ID, educational group, subgroup, and student status were used during preprocessing so that missing demographic values could be filled from the most relevant available context: age and gender were first transferred from other records of the same occupant; remaining missing age values were estimated from the median for the corresponding educational group and student-status combination, with group and global medians used as fallbacks, while remaining missing gender values were assigned by a seeded random draw from the observed gender distribution within the same educational group. "
    "For numeric exposure or context variables, clothing insulation was imputed by the group median, while temperature trend, sound level, and lighting were imputed by subgroup-within-group medians where available and by broader medians otherwise. "
    "Classroom position was retained as the original set of front/back/left/right/middle binary location flags rather than collapsed into a single category; unknown classroom position was defaulted to middle. "
    "The final model-ready data sheet excludes trace columns and imputation metadata, while detailed imputation counts and strategies are retained in the workbook support sheets."
)


def write_dataset(
    path: Path,
    data_before_imputation: pd.DataFrame,
    data: pd.DataFrame,
    target_name: str,
    imputation_summary: pd.DataFrame,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data_before_imputation = enforce_location_boolean_columns(data_before_imputation)
    data = enforce_location_boolean_columns(data)
    data_before_imputation_sheet = model_data_sheet(data_before_imputation, target_name)
    data_sheet = model_data_sheet(data, target_name)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        data_sheet.to_excel(writer, sheet_name="data", index=False)
        data_before_imputation_sheet.to_excel(writer, sheet_name="data_before_imputation", index=False)
        data_dictionary(data_sheet.columns, target_name).to_excel(
            writer,
            sheet_name="data_dictionary",
            index=False,
        )
        missingness_summary(data_before_imputation_sheet).to_excel(writer, sheet_name="missingness_before_imputation", index=False)
        missingness_summary(data_sheet).to_excel(writer, sheet_name="missingness_after_imputation", index=False)
        imputation_summary.to_excel(writer, sheet_name="imputation_summary", index=False)
        pd.DataFrame({"article_paragraph": [IMPUTATION_PARAGRAPH]}).to_excel(
            writer,
            sheet_name="article_imputation_text",
            index=False,
        )


def read_clean_dataset(path: Path, required_columns: Iterable[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Clean dataset not found: {path}")
    data = pd.read_excel(path, sheet_name="data")
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"{path.name}: missing required columns: {missing_columns}")
    return enforce_location_boolean_columns(data)


def main() -> None:
    thermal = read_clean_dataset(THERMAL_INPUT, [*COMMON_METADATA_COLUMNS, *THERMAL_COLUMNS])
    ieq = read_clean_dataset(IEQ_INPUT, [*COMMON_METADATA_COLUMNS, *IEQ_COLUMNS])

    thermal_imputed, thermal_imputation_summary = apply_imputation(thermal, THERMAL_COLUMNS[2:], include_ieq_features=False)
    ieq_imputed, ieq_imputation_summary = apply_imputation(ieq, IEQ_COLUMNS[2:], include_ieq_features=True)

    write_dataset(THERMAL_OUTPUT, thermal, thermal_imputed, "Thermal satisfaction", thermal_imputation_summary)
    write_dataset(IEQ_OUTPUT, ieq, ieq_imputed, "IEQ satisfaction", ieq_imputation_summary)

    print(f"Wrote {THERMAL_OUTPUT} ({len(thermal_imputed):,} rows, {len(model_data_sheet(thermal_imputed, 'Thermal satisfaction').columns):,} data columns)")
    print(f"Wrote {IEQ_OUTPUT} ({len(ieq_imputed):,} rows, {len(model_data_sheet(ieq_imputed, 'IEQ satisfaction').columns):,} data columns)")
    print("Read clean datasets, wrote model-ready datasets, and excluded imputation metadata from the model-data sheets.")


if __name__ == "__main__":
    main()
