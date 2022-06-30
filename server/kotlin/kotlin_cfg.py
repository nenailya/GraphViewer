import pathlib
import re
import shutil

import docker
from docker.errors import ContainerError
import tempfile
import os
from pathlib import Path
import fnmatch


def get_cfg(code: str):
    jar_path = sorted(pathlib.Path('.').glob('**/kt_cfg*.jar'))[0].absolute()
    client = docker.from_env()
    with tempfile.TemporaryDirectory() as dir:
        shutil.copy(jar_path, dir + '/kt_cfg.jar')
        name = Path(dir) / 'Main.kt'
        package = get_package(code)
        with open(name, 'w') as file:
            file.write(code)
        try:
            client.containers.run(
                'zenika/kotlin', command=f"kotlinc Main.kt -d main.jar",
                working_dir='/src', volumes=[f"{dir}:/src"], remove=True)
            _dir = dir.replace('\\', '/')
            client.containers.run(
                'zenika/kotlin', command=f"java -jar kt_cfg.jar {package}",
                working_dir='/src', volumes=[f"{dir}:/src"], remove=True)
        except ContainerError as e:
            raise RuntimeError(e.stderr)
        files = fnmatch.filter(os.listdir(dir), f'dot.txt')
        if len(files) < 1:
            raise RuntimeError('Something wrong')
        else:
            with open(Path(dir) / files[0], 'r') as f:
                return f.read()


def get_package(code: str):
    clear_code = code.strip()
    pattern = re.compile('(?<=^(package ))\s*\S+(?=\s*\n)')
    res = re.search(pattern, clear_code)
    if not res:
        return ""
    else:
        return res.group(0).strip()
