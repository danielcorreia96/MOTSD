# coding=utf-8
import datetime
import os.path
from pathlib import Path

import svn.local
from joblib import Memory

memory = Memory(Path("data"), verbose=0)


@memory.cache
def get_log(branch, from_dt, to_dt):
    repo_path = os.path.abspath(branch)
    client = svn.local.LocalClient(path_=repo_path)

    log = client.log_default(
        timestamp_from_dt=datetime.datetime.fromisoformat(from_dt),
        timestamp_to_dt=datetime.datetime.fromisoformat(to_dt),
        changelist=True,
    )
    return log


@memory.cache()
def get_log_for_revision(branch, revision):
    repo_path = os.path.abspath(branch)
    client = svn.local.LocalClient(path_=repo_path)

    log = client.log_default(
        revision_from=revision, revision_to=revision, changelist=True
    )
    return log
