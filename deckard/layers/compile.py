import pandas as pd
from pathlib import Path
import json
import logging
from tqdm import tqdm
import yaml


logger = logging.getLogger(__name__)


def flatten_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Args:
        df (pd.DataFrame): a dataframe with dictionaries as entries in some columns

    Returns:
        pd.DataFrame: a dataframe with the dictionaries flattened into columns using pd.json_normalize
    """
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    for col in tqdm(df.columns, desc="Flattening columns"):
        if isinstance(df[col][0], dict):
            tmp = pd.json_normalize(df[col])
            tmp.columns = [f"{col}.{subcol}" for subcol in tmp.columns]
            tmp.index = df.index
            df = pd.merge(df, tmp, left_index=True, how="outer", right_index=True)
            if f"files.{col}_file" in tmp:
                df[col] = Path(tmp[f"files.{col}_file"]).apply(lambda x: x.stem)
            else:
                df[col] = tmp.index
        else:
            df = pd.concat([df, df[col]], axis=1)
    return df


def parse_folder(folder, files=["params.yaml", "score_dict.json"]) -> pd.DataFrame:
    """
    Parse a folder containing files and return a dataframe with the results, excluding the files in the exclude list.
    :param folder: Path to folder containing files
    :param files: List of files to parse. Defaults to ["params.yaml", "score_dict.json"]. Other files will be added as columns with hrefs.
    :return: Pandas dataframe with the results
    """
    folder = Path(folder)

    logger.debug(f"Parsing folder {folder}...")
    path_gen = []
    for file in files:
        path_gen.extend(folder.glob(f"**/{file}"))
    path_gen.sort()
    path_gen = list(set(path_gen))
    path_gen.sort()
    folder_gen = map(lambda x: x.parent, path_gen)
    folder_gen = set(folder_gen)
    results = {}
    for file in tqdm(path_gen, desc="Parsing Specified files"):
        results = read_file(file, results)
    for folder in tqdm(folder_gen, desc="Adding other files to results"):
        results = add_file(folder, path_gen, results)
    df = pd.DataFrame(results).T
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.columns = df.columns.str.strip()
    return df


def add_file(folder, path_gen, results):
    all_files = Path(folder).glob("**/*")
    for file in all_files:
        if file not in path_gen:
            if file.parent.name not in results:
                results[file.parent.name] = {}
            results[file.parent.name][file.stem] = file
    return results


def read_file(file, results):
    suffix = file.suffix
    folder = file.parent.name
    stage = file.parent.parent.name
    if folder not in results:
        results[folder] = {}
    if suffix == ".json":
        with open(file, "r") as f:
            try:
                dict_ = json.load(f)
            except json.decoder.JSONDecodeError as e:
                raise e
    elif suffix == ".yaml":
        with open(file, "r") as f:
            dict_ = yaml.safe_load(f)
    else:
        raise ValueError(f"File type {suffix} not supported.")
    results[folder]["stage"] = stage
    results[folder].update(dict_)
    return results


def parse_results(folder, files=["score_dict.json", "params.yaml"]):
    df = parse_folder(folder, files=files)
    df = flatten_results(df)
    return df


def save_results(results, results_file, results_folder) -> str:
    """
    Compile results from a folder of reports and save to a csv file; return the path to the csv file. It will optionally delete columns from the results.
    """
    results_file = Path(results_folder, results_file)
    logger.info(f"Saving data to {results_file}")
    Path(results_folder).mkdir(exist_ok=True, parents=True)
    suffix = results_file.suffix
    if suffix == ".csv":
        results.to_csv(results_file)
    elif suffix == ".xlsx":
        results.to_excel(results_file)
    elif suffix == ".html":
        results.to_html(results_file)
    elif suffix == ".json":
        results.to_json(results_file)
    else:
        raise ValueError(f"File type {suffix} not supported.")
    assert Path(
        results_file,
    ).exists(), f"Results file {results_file} does not exist. Something went wrong."
    return results_file


def load_results(results_file, results_folder) -> pd.DataFrame:
    """
    Load results from a csv file; return the path to the csv file. It will optionally delete columns from the results.
    """
    results_file = Path(results_folder, results_file)
    logger.info(f"Loading data from {results_file}")
    Path(results_folder).mkdir(exist_ok=True, parents=True)
    suffix = results_file.suffix
    if suffix == ".csv":
        results = pd.read_csv(results_file)
    elif suffix == ".xlsx":
        results = pd.read_excel(results_file)
    elif suffix == ".html":
        results = pd.read_html(results_file)
    elif suffix == ".json":
        results = pd.read_json(results_file)
    else:
        raise ValueError(f"File type {suffix} not supported.")
    assert Path(
        results_file,
    ).exists(), f"Results file {results_file} does not exist. Something went wrong."
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--results_file", type=str, default="results.csv")
    parser.add_argument("--report_folder", type=str, default="reports", required=True)
    parser.add_argument("--results_folder", type=str, default=".")
    parser.add_argument("--config", type=str, default="conf/compile.yaml")
    parser.add_argument("--exclude", type=list, default=None, nargs="*")
    parser.add_argument("--verbose", type=str, default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=args.verbose)
    report_folder = args.report_folder
    results_file = args.results_file
    results_folder = args.results_folder
    results = parse_results(report_folder)
    report_file = save_results(results, results_file, results_folder)
    assert Path(
        report_file,
    ).exists(), f"Results file {report_file} does not exist. Something went wrong."
