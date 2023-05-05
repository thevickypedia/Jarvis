import collections
import contextlib
import logging

import uvicorn
import yaml
from yaml.dumper import Dumper
from yaml.nodes import Node


class APIServer(uvicorn.Server):
    """Shared servers state that is available between all protocol instances.

    >>> APIServer

    See Also:
        Overrides `uvicorn.server.Server <https://github.com/encode/uvicorn/blob/master/uvicorn/server.py#L48>`__

    References:
        https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
    """

    def install_signal_handlers(self) -> None:
        """Overrides ``install_signal_handlers`` in ``uvicorn.Server`` module."""
        pass

    @contextlib.contextmanager
    def run_in_parallel(self) -> None:
        """Initiates ``Server.run`` in a dedicated process."""
        self.run()


def ordered_load(stream,
                 Loader=yaml.SafeLoader,  # noqa
                 object_pairs_hook=collections.OrderedDict) -> collections.OrderedDict:  # noqa
    """Custom loader for OrderedDict.

    Args:
        stream: FileIO stream.
        Loader: Yaml loader.
        object_pairs_hook: OrderedDict object.

    Returns:
        OrderedDict:
        Dictionary after loading yaml file.
    """

    class OrderedLoader(Loader):
        """Overrides the built-in Loader.

        >>> OrderedLoader

        """

        pass

    def construct_mapping(loader: Loader, node: Node) -> collections.OrderedDict:
        """Create a mapping for the constructor."""
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        tag=yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        constructor=construct_mapping
    )

    return yaml.load(stream=stream, Loader=OrderedLoader)


def ordered_dump(data, stream=None, Dumper=yaml.SafeDumper, **kwds) -> 'Dumper':  # noqa
    """Custom dumper to serialize OrderedDict.

    Args:
        data: Data to be dumped into yaml file.
        stream: FileIO stream.
        Dumper: Yaml dumper.
        kwds: Keyword arguments like indent.

    Returns:
        Dumper:
        Response from yaml Dumper.
    """

    class OrderedDumper(Dumper):
        """Overrides the built-in Dumper.

        >>> OrderedDumper

        """

        pass

    def _dict_representer(dumper: Dumper, data: dict) -> Node:  # noqa
        """Overrides built-in representer.

        Args:
            dumper: yaml dumper.
            data: data to be dumped.

        Returns:
            Node:
            Returns the representer node.
        """
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items()
        )

    OrderedDumper.add_representer(data_type=collections.OrderedDict, representer=_dict_representer)
    return yaml.dump(data=data, stream=stream, Dumper=OrderedDumper, **kwds)


class AddProcessName(logging.Filter):
    """Wrapper that overrides ``logging.Filter`` to add ``processName`` to the existing log format.

    >>> AddProcessName

    """

    def __init__(self, process_name: str):
        """Instantiates super class.

        Args:
            process_name: Takes name of the process to be added as argument.
        """
        self.process_name = process_name
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """Overrides the built-in filter record."""
        record.processName = self.process_name
        return True
