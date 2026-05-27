from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def find_raw_dataset() -> Path:
    candidates = [
        ROOT.parent / "02_Datasets" / "raw" / "FullDataset_CombinedSimple.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Raw dataset not found. Checked: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


RAW_DATASET = find_raw_dataset()

DATASET_DIR = ROOT.parent / "02_Datasets"
THERMAL_OUTPUT = DATASET_DIR / "clean" / "thermal_comfort_clean_dataset.xlsx"
IEQ_OUTPUT = DATASET_DIR / "clean" / "ieq_clean_dataset.xlsx"

CLO_SIMPLE_TO_NUMERIC = {"lightly": 0.44, "neutral": 0.64, "warmly": 0.81}
CASE_STUDY_TO_GROUP = {
    "PrimarySchool": "Primary school",
    "SecondarySchool": "Secondary school",
    "TLR": "Test lecture room",
}

POSITION_COLUMNS = {
    "LocationBack": "LocationBack",
    "LocationFront": "LocationFront",
    "LocationLeft": "LocationLeft",
    "LocationRight": "LocationRight",
    "LocationMiddle": "LocationMiddle",
}

COMMON_METADATA_COLUMNS = ["source_row_number", "TimeVote", "Occupant ID", "Group", "Subgroup", "Student"]

THERMAL_COLUMNS = [
    "Thermal satisfaction",
    "Thermal satisfaction 3-class",
    "Temperature",
    "RH",
    "CLO",
    "Age",
    "Gender",
    "EA",
    "LocationBack",
    "LocationFront",
    "LocationLeft",
    "LocationRight",
    "LocationMiddle",
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
    "LocationBack",
    "LocationFront",
    "LocationLeft",
    "LocationRight",
    "LocationMiddle",
    "Ttrend",
    "Vote hour",
    "Vote weekday",
    "Moment",
    "AC on/off",
]


def numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.replace(",", ".", regex=False), errors="coerce")


def add_clo(frame: pd.DataFrame) -> pd.Series:
    detailed = numeric_series(frame["CLO_Detailed"]) if "CLO_Detailed" in frame.columns else pd.Series(np.nan, index=frame.index)
    if "CLO_Simple" in frame.columns:
        simple_text = frame["CLO_Simple"].astype("string").str.strip().str.lower()
        simple = simple_text.map(CLO_SIMPLE_TO_NUMERIC)
    else:
        simple = pd.Series(np.nan, index=frame.index)
    return detailed.fillna(simple)


def is_positive_location_value(value: object) -> bool:
    if pd.isna(value):
        return False
    text = str(value).strip().lower()
    return text in {"1", "1.0", "true", "yes", "y", "x", "back", "front", "left", "right", "middle"}


def normalize_location_flag(series: pd.Series) -> pd.Series:
    result = pd.Series(pd.NA, index=series.index, dtype="boolean")
    result.loc[series.notna()] = series.loc[series.notna()].map(is_positive_location_value).astype("boolean")
    return result


def enforce_location_boolean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in POSITION_COLUMNS.values():
        if column in result.columns:
            result[column] = result[column].astype("boolean")
    return result


def add_time_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    vote_time = pd.to_datetime(result["TimeVote"], errors="coerce", dayfirst=True)
    result["Vote hour"] = vote_time.dt.hour
    result["Vote weekday"] = vote_time.dt.day_name()
    return result


def normalize_categorical(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    return text.replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "none": pd.NA})


def normalize_student_status(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series:
        if pd.isna(value):
            normalized.append("Unknown")
        elif bool(value):
            normalized.append("Student")
        else:
            normalized.append("Teacher/staff")
    return pd.Series(normalized, index=series.index, dtype="string")


def satisfaction_three_class(series: pd.Series) -> pd.Series:
    votes = pd.to_numeric(series, errors="coerce")
    labels = pd.Series(pd.NA, index=series.index, dtype="string")
    labels.loc[votes.isin([1, 2])] = "dissatisfied"
    labels.loc[votes == 3] = "neutral"
    labels.loc[votes.isin([4, 5])] = "satisfied"
    return labels


def build_base_frame(raw: pd.DataFrame) -> pd.DataFrame:
    base = pd.DataFrame(index=raw.index)
    base["source_row_number"] = np.arange(1, len(raw) + 1)
    base["TimeVote"] = raw["TimeVote"]
    base["Occupant ID"] = normalize_categorical(raw["ID"])
    base["Group"] = normalize_categorical(raw["CaseStudy"]).map(CASE_STUDY_TO_GROUP).fillna(normalize_categorical(raw["CaseStudy"]))
    base["Subgroup"] = normalize_categorical(raw["Subgroup"])
    base["Student"] = normalize_student_status(raw["Student"])
    base["Thermal satisfaction"] = numeric_series(raw["ThermalSatisfaction"])
    base["IEQ satisfaction"] = numeric_series(raw["IEQSatisfaction"])
    base["Thermal satisfaction 3-class"] = satisfaction_three_class(base["Thermal satisfaction"])
    base["IEQ satisfaction 3-class"] = satisfaction_three_class(base["IEQ satisfaction"])
    base["Temperature"] = numeric_series(raw["Troom"])
    base["RH"] = numeric_series(raw["RH"])
    base["CLO"] = add_clo(raw)
    base["CO2"] = numeric_series(raw["CO2"])
    base["Lighting"] = numeric_series(raw["Lighting"])
    base["Sound"] = numeric_series(raw["Sound"])
    base["Age"] = numeric_series(raw["Age"])
    base["Gender"] = normalize_categorical(raw["Gender"])
    base["EA"] = numeric_series(raw["EA"])
    for raw_column, output_column in POSITION_COLUMNS.items():
        base[output_column] = normalize_location_flag(raw[raw_column])
    base["Ttrend"] = numeric_series(raw["Ttrend"])
    base["Moment"] = normalize_categorical(raw["Moment"])
    base["AC on/off"] = normalize_categorical(raw["AC_Classroom"])
    base = add_time_features(base)
    return base


def data_dictionary(columns: Iterable[str], target_name: str) -> pd.DataFrame:
    roles = {column: "input" for column in columns}
    roles[target_name] = "original output"
    for column in columns:
        if column.endswith("3-class"):
            roles[column] = "primary modeling output"
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
    }
    rows = []
    for column in columns:
        rows.append(
            {
                "column": column,
                "role": roles.get(column, "input"),
                "description": descriptions.get(column, ""),
            }
        )
    return pd.DataFrame(rows)


def missingness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = frame.isna().sum().rename("missing_rows").to_frame()
    summary["total_rows"] = len(frame)
    summary["complete_rows"] = summary["total_rows"] - summary["missing_rows"]
    summary["missing_percent"] = (summary["missing_rows"] / len(frame) * 100).round(2)
    summary["complete_percent"] = (summary["complete_rows"] / len(frame) * 100).round(2)
    return summary.reset_index(names="column")


def write_dataset(path: Path, data: pd.DataFrame, target_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = enforce_location_boolean_columns(data)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="data", index=False)
        data_dictionary(data.columns, target_name).to_excel(
            writer,
            sheet_name="data_dictionary",
            index=False,
        )
        missingness_summary(data).to_excel(writer, sheet_name="missingness_summary", index=False)


def main() -> None:
    raw = pd.read_csv(RAW_DATASET)
    base = build_base_frame(raw)

    thermal = base[[*COMMON_METADATA_COLUMNS, *THERMAL_COLUMNS]].copy()
    ieq = base[[*COMMON_METADATA_COLUMNS, *IEQ_COLUMNS]].copy()

    write_dataset(THERMAL_OUTPUT, thermal, "Thermal satisfaction")
    write_dataset(IEQ_OUTPUT, ieq, "IEQ satisfaction")

    print(f"Wrote {THERMAL_OUTPUT} ({len(thermal):,} rows, {len(thermal.columns):,} columns)")
    print(f"Wrote {IEQ_OUTPUT} ({len(ieq):,} rows, {len(ieq.columns):,} columns)")
    print("No rows were dropped and no missing values were imputed in this clean-data step.")


if __name__ == "__main__":
    main()
