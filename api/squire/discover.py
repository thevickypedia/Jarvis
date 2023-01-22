import os
import pathlib
import warnings
from importlib import import_module
from typing import Iterable, List

from fastapi import APIRouter

from api.squire.logger import logger


class Entrypoint:
    """Wrapper for Entrypoint object.

    >>> Entrypoint

    """

    def __init__(self, module: str, stem: str):
        """Wraps entry point into an object.

        Args:
            module: Router path in the form of a module.
            stem: Bare name of the module.
        """
        self.module = module
        self.stem = stem


def get_entrypoints(package: str, routers: str) -> Iterable[Entrypoint]:
    """Get all the routers as a module that can be imported.

    Args:
        package: Directory name of the package.
        routers: Directory name where the potential router modules are present.

    See Also:
        The attribute within the module should be named as ``router`` for the auto discovery to recognize.

    Warnings:
        This is a crude way of scanning modules for routers.

    Yields:
        Iterable[Entrypoint]:
        Entrypoint object with router module and the bare name of it.
    """
    for __path, __directory, __file in os.walk(routers):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            stem = pathlib.PurePath(file_).stem
            breaker = pathlib.PurePath(os.path.join(__path, stem)).parts
            # Replace paths with . to make it appear as a module
            yield Entrypoint(module='.'.join(breaker[breaker.index(package):]), stem=stem)


def routes(package: str, routers: str) -> Iterable[APIRouter]:
    """Scans routers directory to import all the routers available.

    Args:
        package: Directory name of the package.
        routers: Directory name where the potential router modules are present.

    Yields:
        Iterable[APIRouter]:
        API Router from scanned modules.
    """
    entrypoints: List[Entrypoint] = sorted(list(get_entrypoints(package=package, routers=routers)),
                                           key=lambda ent: ent.stem)  # sort by name of the route
    for entrypoint in entrypoints:
        try:
            route = import_module(entrypoint.module)
        except ImportError as error:
            logger.error(error)
            warnings.warn(error.__str__())
            continue
        if hasattr(route, 'router'):
            logger.info(f"Loading router: {entrypoint.module}")
            yield getattr(route, 'router')
        else:
            warnings.warn(f'{route.__name__} is missing the router attribute.')
