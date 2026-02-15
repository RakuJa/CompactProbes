#!/usr/bin/env python3

import re
import numpy as np
import pandas as pd
from typing import List, Tuple
from tqdm.autonotebook import tqdm
import argparse


def calculate_filter_size_and_interval(filter_string: str) -> Tuple[int, int]:
    """
    Calculate filter size and interval from filter string pattern.

    Example: "0[8] ooooxxxx 0[1768]"
    - 0[8] = 8 zeros before (interval/offset = 8)
    - ooooxxxx = 8 character filter (filter_size = 8)
    - 0[1768] = 1768 zeros after

    Args:
        filter_string: Filter pattern string

    Returns:
        Tuple of (filter_size, interval)
    """
    parts = filter_string.split()

    interval = 0
    filter_size = 0

    for part in parts:
        if part.startswith("0["):
            # This is a zero padding
            count = int(part[2:-1])
            if filter_size == 0:
                # Zeros before the filter = interval
                interval = count
        else:
            # This is the actual filter (o's and x's)
            filter_size = len(part)

    return filter_size, interval


def parse_log_file(filename: str) -> pd.DataFrame:
    """
    Parse bamboo log file to extract filter configurations.

    Args:
        filename: Path to the bamboo log file

    Returns:
        DataFrame with columns: Best Filter, Best Threshold, Min Error, Confidence,
                                Filter Size, Interval
    """
    data = []

    with open(filename, "r") as file:
        lines = file.readlines()

        current_filter = None
        current_threshold = None
        current_min_error = None
        current_confidence = None

        for line in lines:
            if "Best Filter" in line:
                filter_match = re.search(r"Best Filter: (.+)", line)
                if filter_match:
                    current_filter = filter_match.group(1).strip()

            elif "Best Threshold" in line:
                threshold_match = re.search(r"Best Threshold: (.+)", line)
                if threshold_match:
                    current_threshold = int(threshold_match.group(1).strip())

            elif "Min error" in line:
                min_error_match = re.search(r"Min error: (.+)", line)
                if min_error_match:
                    current_min_error = float(min_error_match.group(1).strip())

            elif "Confidence" in line:
                confidence_match = re.search(r"Confidence: (.+)", line)
                if confidence_match:
                    current_confidence = float(confidence_match.group(1).strip())

                    # Calculate filter size and interval from the filter string
                    filter_size, interval = calculate_filter_size_and_interval(current_filter)

                    # Add to data list
                    data.append(
                        (
                            current_filter,
                            current_threshold,
                            current_min_error,
                            current_confidence,
                            filter_size,
                            interval,
                        )
                    )

                    # Reset current values for the next entry
                    current_filter = None
                    current_threshold = None
                    current_min_error = None
                    current_confidence = None

    # Convert the list of tuples into a DataFrame
    df = pd.DataFrame(
        data, columns=["Best Filter", "Best Threshold", "Min Error", "Confidence",
                       "Filter Size", "Interval"]
    )

    return df


def extract_filter_size_and_intervals(log_file: str) -> List[Tuple[int, int]]:
    """
    Extract (filter_size, interval) tuples from bamboo log file.
    This replaces the hardcoded data array.

    Args:
        log_file: Path to bamboo log file

    Returns:
        List of (filter_size, interval) tuples
    """
    df = parse_log_file(log_file)

    # Check if Filter Size and Interval columns exist and have valid data
    if "Filter Size" in df.columns and "Interval" in df.columns:
        data = []
        for _, row in df.iterrows():
            fs = row["Filter Size"]
            interval = row["Interval"]

            # Convert to int if not None/NaN
            if pd.notna(fs) and pd.notna(interval):
                data.append((int(fs), int(interval)))

        return data
    else:
        print("Filter Size and/or Interval not found in log file.")
        print("Available columns:", df.columns.tolist())
        return []


def convert_column_to_array(df: pd.DataFrame, column_name: str) -> np.ndarray:
    """
    Convert a DataFrame column of strings to a numpy array of character lists.

    Args:
        df: Input DataFrame
        column_name: Name of the column to convert

    Returns:
        Numpy array where each row is a list of characters
    """
    return np.array([list(bstr) for bstr in df[column_name]])


def generate_string_pair_df(pairs_df: pd.DataFrame, dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a DataFrame with string pairs from indices.

    Args:
        pairs_df: DataFrame with columns 'Item 1', 'Item 2', 'Equality'
        dataset: DataFrame containing the actual string data

    Returns:
        DataFrame with Item 1, Item 2 (as arrays), and Equality columns
    """
    # Convert the concatenated column to a numpy array
    dataset_array = convert_column_to_array(dataset, "concatenated")

    return_df = pd.DataFrame()

    # Import the items into the pairs_df dataframe
    return_df["Item 1"] = pairs_df["Item 1"].apply(lambda index: dataset_array[index])
    return_df["Item 2"] = pairs_df["Item 2"].apply(lambda index: dataset_array[index])
    return_df["Equality"] = pairs_df["Equality"]

    return return_df


def filter_parser(input_string: str) -> List[int]:
    """
    Parse a filter string into a list of integers.

    Format:
    - 'o' represents -1
    - 'x' represents 1
    - '0[n]' represents n zeros

    Args:
        input_string: Filter string to parse

    Returns:
        List of integers representing the filter
    """
    # Split the string into its parts
    parts = input_string.split()

    # Initialize the final array
    result = []

    # Process each part
    for part in parts:
        if part.startswith("0["):
            # Extract the number inside the brackets
            count = int(part[2:-1])
            # Append the corresponding number of zeros to the result
            result.extend([0] * count)
        else:
            # Translate the tiles to their respective values
            for char in part:
                if char == "o":
                    result.append(-1)
                elif char == "x":
                    result.append(1)

    return result


def hamming_distance(array1: List, array2: List) -> int:
    """
    Calculate Hamming distance between two arrays.

    Args:
        array1: First array
        array2: Second array

    Returns:
        Hamming distance (number of differing positions)
    """
    # Check if arrays have the same length
    if len(array1) != len(array2):
        raise ValueError("Arrays must have the same length")

    # Initialize distance counter
    distance = 0

    # Iterate through arrays and count differences
    for i in range(len(array1)):
        if array1[i] != array2[i]:
            distance += 1

    return distance


def calculate_single_fprint(item: np.ndarray,
                            best_filters: List[str],
                            best_thresholds: List[int]) -> List[int]:
    """
    Calculate fingerprint for a single item using given filters and thresholds.

    Args:
        item: Input array to fingerprint
        best_filters: List of filter strings
        best_thresholds: List of threshold values

    Returns:
        List of fingerprint bits (1 or -1)
    """
    fingerprint = []

    for best_filter, best_threshold in zip(best_filters, best_thresholds):
        filtered = np.sum(np.multiply(item.astype(int), filter_parser(best_filter)))

        if filtered > best_threshold:
            filtered = 1
        else:
            filtered = -1

        fingerprint.append(filtered)

    return fingerprint


def print_filter_config_as_code(data: List[Tuple[int, int]]) -> None:
    """
    Print filter configuration as Python code (replaces hardcoded data).

    Args:
        data: List of (filter_size, interval) tuples
    """
    print("\n# Copy this results into the notebook (data_fabio/data) on training notebooks:\n")
    print("BAMBOO selected intervals and filter size")
    print("data = [")
    for fs, interval in data:
        print(f"    ({fs}, {interval}),")
    print("]")
    print(f"Total filters: {len(data)}")

    if data:
        filter_sizes = [fs for fs, _ in data]
        intervals = [i for _, i in data]
        print(f"Unique filter sizes: {sorted(set(filter_sizes))}")
        print(f"Interval range: {min(intervals)} - {max(intervals)}")
        print(f"Average interval: {sum(intervals) / len(intervals):.2f}")


def extract_pairs_with_fingerprints(
        log_file: str,
        string_csv: str,
        pairs_csv: str,
        output_csv: str,
        M_values: List[int] = None,
        max_filters: int = 0
) -> pd.DataFrame:
    if M_values is None:
        M_values = [8, 16, 32, 64]

    print("Loading data...")
    string_df = pd.read_csv(string_csv, dtype=str)
    balanced_pairs_df = pd.read_csv(pairs_csv, index_col=0)

    balanced_pairs_df.drop_duplicates(inplace=True)
    balanced_pairs_df.reset_index(drop=True, inplace=True)

    print("Parsing bamboo log file...")
    best_configs_df = parse_log_file(log_file)
    print(f"Found {len(best_configs_df)} filter configurations")

    if max_filters != 0:
        best_configs_df = best_configs_df.head(max_filters)
        M = max_filters
    else:
        M = len(best_configs_df)

    compression_rate = len(string_df["concatenated"].iloc[0]) / best_configs_df.shape[0]
    print(f"Compression Rate: {compression_rate:.2f}")

    print("Generating string pairs...")
    matrix_pairs_df = generate_string_pair_df(balanced_pairs_df, string_df)
    matrix_pairs_df.reset_index(inplace=True, drop=True)

    best_filters = best_configs_df["Best Filter"].tolist()
    best_thresholds = best_configs_df["Best Threshold"].tolist()

    print("Calculating fingerprints...")
    matrix_pairs_df["fprint1"] = matrix_pairs_df["Item 1"].apply(
        lambda item: calculate_single_fprint(item, best_filters, best_thresholds)
    )
    matrix_pairs_df["fprint2"] = matrix_pairs_df["Item 2"].apply(
        lambda item: calculate_single_fprint(item, best_filters, best_thresholds)
    )

    print("Calculating Hamming distances...")
    for m in tqdm(M_values, desc="Processing M values"):
        if m <= M:
            matrix_pairs_df[f"h_distance_{m}"] = matrix_pairs_df.apply(
                lambda row: hamming_distance(
                    row["fprint1"][:m], row["fprint2"][:m]
                ),
                axis=1,
            )
            print(f"Calculated Hamming distances for M={m}")
        else:
            print(f"Skipping M={m} (exceeds available filters: {M})")

    print(f"\nSaving results to {output_csv}...")
    matrix_pairs_df.to_csv(output_csv, index=False)

    return matrix_pairs_df


def main():
    parser = argparse.ArgumentParser(
        description="Extract BAMBOO configurations and generate fingerprints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--log-file",
        default="bamboo.log",
        help="Path to bamboo log file (default: bamboo.log)"
    )
    parser.add_argument(
        "--string-csv",
        default="data/train_test/bin_test0_new.csv",
        help="Path to CSV containing string data"
    )
    parser.add_argument(
        "--pairs-csv",
        default="data/train_test/bin_test_pairs_new.csv",
        help="Path to CSV containing pairs"
    )
    parser.add_argument(
        "--output-csv",
        default="data/bamboo_filters/bamboo_fingerprint_matrix_pairs.csv",
        help="Path to save output CSV"
    )
    parser.add_argument(
        "--m-values",
        nargs="+",
        type=int,
        default=[8, 16, 32, 64],
        help="List of M values for Hamming distance calculation (default: 8 16 32 64)"
    )
    parser.add_argument(
        "--max-filters",
        type=int,
        default=0,
        help="Maximum number of filters to use, 0 = use all (default: 0)"
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only extract filter size and interval data from log (don't process pairs)"
    )

    args = parser.parse_args()

    # Check if log file exists
    import os
    if not os.path.exists(args.log_file):
        print(f"Error: Log file '{args.log_file}' not found, provide a valid one!")
        return 1

    if args.extract_only:
        data = extract_filter_size_and_intervals(args.log_file)
        if data:
            print_filter_config_as_code(data)
        else:
            configs_df = parse_log_file(args.log_file)
            print(f"\nExtracted {len(configs_df)} filter configurations:")
            print(configs_df[["Best Filter", "Best Threshold", "Min Error", "Confidence"]].head())

    else:
        result_df = extract_pairs_with_fingerprints(
            log_file=args.log_file,
            string_csv=args.string_csv,
            pairs_csv=args.pairs_csv,
            output_csv=args.output_csv,
            M_values=args.m_values,
            max_filters=args.max_filters
        )

        print(f"\nOutput saved to: {args.output_csv}")
        print(f"Processed {len(result_df)} pairs")

        data = extract_filter_size_and_intervals(args.log_file)
        if data:
            print(f"Extracted {len(data)} filter configurations (filter_size, interval):")
            print(f"First 5: {data[:5]}")
            print(f"Last 5: {data[-5:]}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())