import logging
import os
from copy import deepcopy
from pathlib import Path
import dvc.api
import yaml
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf
import hydra
from ..base.utils import flatten_dict, my_hash, unflatten_dict

logger = logging.getLogger(__name__)

__all__ = ["get_params", "save_stage_params", "find_stage_params", "optimise"]


def find_stage_params(params_file, pipeline_file, stage, working_dir, **kwargs):
    if stage is None:
        stages = None
    elif isinstance(stage, str):
        stages = [stage]
    else:
        assert isinstance(stage, list), f"Expected str or list, got {type(stage)}"
        stages = stage
    working_dir = Path(working_dir).resolve()
    old_params = dvc.api.params_show(params_file, stages=[stage], repo=working_dir)
    old_params = flatten_dict(old_params)
    new_params = flatten_dict(kwargs)
    new_trunc_keys = [".".join(key.split(".")[:-1]) for key in new_params.keys()]
    params = {}
    for key in old_params:
        trunc = ".".join(key.split(".")[:-1]) if len(key.split(".")) > 1 else key
        if trunc in new_trunc_keys and key in new_params:
            params[key] = new_params[key]
        else:
            params[key] = old_params[key]
    # Setup the files
    params = unflatten_dict(params)
    params["files"] = {}
    files = dvc.api.params_show(pipeline_file, stages=stages, repo=working_dir)
    unflattened_files = unflatten_dict(files).pop("files", {})
    params["files"].update(**unflattened_files)
    params["files"].update(**{"_target_": "deckard.base.files.FileConfig"})
    return params


def get_params(
    cfg,
    params_file="params.yaml",
    pipeline_file="dvc.yaml",
    working_dir=Path().resolve().as_posix(),
):
    if isinstance(cfg, dict):
        pass
    elif isinstance(cfg, list):
        cfg = unflatten_dict(cfg)
    else:
        raise TypeError(f"Expected dict or list, got {type(cfg)}")
    stage = cfg.pop("stage", None)
    if stage is not None and stage.startswith("+stage="):
        stage = stage.split("=")[-1]
    cfg = find_stage_params(
        params_file=params_file,
        pipeline_file=pipeline_file,
        working_dir=working_dir,
        stage=stage,
        **cfg,
    )
    id_ = my_hash(cfg)
    cfg.update({"_target_": "deckard.base.experiment.Experiment"})

    if "attack_file" in cfg["files"] and cfg["files"]["attack_file"] is not None:
        cfg["files"]["attack_file"] = str(
            Path(cfg["files"]["attack_file"])
            .with_name(my_hash(cfg["attack"]))
            .as_posix(),
        )
    if "model_file" in cfg["files"] and cfg["files"]["model_file"] is not None:
        cfg["files"]["model_file"] = str(
            Path(cfg["files"]["model_file"])
            .with_name(my_hash(cfg["model"]))
            .as_posix(),
        )
    if "data_file" in cfg["files"] and cfg["files"]["data_file"] is not None:
        cfg["files"]["data_file"] = str(
            Path(cfg["files"]["data_file"]).with_name(my_hash(cfg["data"])).as_posix(),
        )
    cfg["files"]["_target_"] = "deckard.base.files.FileConfig"
    cfg["files"]["name"] = id_
    if stage is not None:
        cfg["files"]["stage"] = stage
    return cfg


def save_stage_params(cfg, folder, params_file):
    path = Path(folder, Path(params_file).name)
    with open(path, "w") as f:
        yaml.safe_dump(cfg, f)
    assert Path(path).exists()


def optimise(cfg: DictConfig) -> None:
    cfg = OmegaConf.to_container(OmegaConf.create(cfg), resolve=True)
    scorer = cfg.pop("optimizers", None)
    direction = cfg.pop("direction", "maximize")
    cfg = get_params(cfg)
    exp = instantiate(cfg)
    files = deepcopy(exp.files)()
    folder = Path(files["score_dict_file"]).parent
    Path(folder).mkdir(exist_ok=True, parents=True)
    save_stage_params(cfg, folder, "params.yaml")
    id_ = Path(files["score_dict_file"]).parent.name
    try:
        scores = exp()
        if isinstance(scorer, str):
            score = scores[scorer]
        elif isinstance(scorer, list):
            direction = cfg.pop("direction", "maximize")
            score = [scores[s] for s in scorer]
        elif scorer is None:
            score = list(scores.values())[0]
        else:
            raise TypeError(f"Expected str or list, got {type(scorer)}")
    except Exception as e:
        logger.warning(
            f"Exception {e} occured while running experiment {id_}. Setting score to 0.",
        )
        if direction == "minimize":
            score = 1e10
        else:
            score = -1e10
        raise e
    return score


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    config_path = os.environ.pop(
        "DECKARD_CONFIG_PATH",
        str(Path(Path(), "conf").absolute().as_posix()),
    )
    config_name = os.environ.pop("DECKARD_DEFAULT_CONFIG", "default.yaml")

    @hydra.main(config_path=config_path, config_name=config_name, version_base="1.3")
    def hydra_optimise(cfg: DictConfig) -> float:
        score = optimise(cfg)
        return score

    hydra_optimise()