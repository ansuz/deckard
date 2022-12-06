import argparse
import logging
import subprocess
import sys

# Suppress user warning
import warnings
from os import chdir, getcwd
from pathlib import Path

# import dvc.api

import deckard  # noqa: F401

warnings.filterwarnings("ignore")


if __name__ == "__main__":
    print("Deckard: Toolbox for adversarial machine learning.")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        help="Path to the directory containing the files to be processed",
        default=".",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="verbosity level",
        action="store_true",
        default="DEBUG",
    )
    parser.add_argument(
        "-p",
        "--pipeline",
        help="Path to the pipeline to be used",
        default="dvc.yaml",
    )
    parser.add_argument(
        "-c",
        "--configuration",
        help="Configuration file for the experiment",
        default=None,
    )
    parser.add_argument(
        "--force",
        help="Force execution of the pipeline",
        action="store_true",
        default=True,
    )
    args = parser.parse_args()
    logger = logging.getLogger()
    logger.setLevel(args.verbose)
    path = Path(args.path)
    assert path.exists(), f"Path {path} does not exist"
    assert path.is_dir(), f"Path {path} is not a directory"
    assert Path(
        args.path,
        args.pipeline,
    ).exists(), f"Pipeline {args.pipeline} does not exist in {path}"
    chdir(Path(args.path).resolve())
    print(f"Changed directory to {path.resolve()}")

    dag_cmd = "dvc dag"
    print(f"Running: {dag_cmd}")
    # run command and wait for it to finish
    out = subprocess.run(
        dag_cmd,
        shell=True,
        check=True,
        stdout=sys.stdout,
        universal_newlines=True,
        stderr=sys.stderr,
    )
    print(out)
    print("Pipeline: %s", args.pipeline)

    if args.configuration is not None:
        raise NotImplementedError("Configuration file not yet implemented")
    else:
        print("Processing pipeline %s" % args.pipeline)
        print("Working Directory: %s" % getcwd())
        pipeline_command = f"dvc repro {args.pipeline} --verbose"
        if args.force:
            pipeline_command += " --force"
        print("Pipeline: %s" % pipeline_command)
        print("Running pipeline. This may take a while...")
        subprocess.run(pipeline_command, stderr=sys.stderr, stdout=sys.stdout)
        print("Pipeline: done")
    print("Results are in %s" % path.resolve())
