import subprocess
from typing import Dict, List

from modules.exceptions import CameraError
from modules.models.classes import settings

Windows = """wmic path CIM_LogicalDevice where "Description like 'USB Video%'" get /value"""
Darwin = "system_profiler SPCameraDataType"


def list_splitter(original_list: List[str], delimiter: str) -> List[List[str]]:
    """Splits a list into multiple lists at a specific value given.

    Notes:
        delimiter: This value should be final value where the initial list must be split.

    See Also:
        .. code-block:: python

            main_list = ['First Name', 'Vignesh', 'Last Name', 'Rao', 'Drives', 'Jaguar',
                         'First Name', 'Tony', 'Last Name', 'Stark', 'Drives', 'Mark III']

        - delimiter should be ``Drives`` since that's where the main list has to be split.

    Args:
        original_list: List that has to be split.
        delimiter: Value where the list has to be split.

    Returns:
        List[List[str]]:
        Returns list of list(s).
    """
    # Split indices at the required value where the list as to be split and rebuilt as a new one
    split_indices = [index + 1 for index, val in enumerate(original_list) if val.startswith(delimiter)]

    # Rebuild the new list split at the given index value
    return [original_list[i: j] for i, j in
            zip([0] + split_indices,
                split_indices + ([len(original_list)] if split_indices[-1] != len(original_list) else []))]


class Camera:
    """Initiates camera object to get information about the connected cameras.

    >>> Camera

    """

    def __init__(self):
        """Instantiates the camera object to run the OS specific builtin commands to get the camera information."""
        cmd = Darwin if settings.macos else Windows

        self.output, err = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).communicate()
        if error := err.decode(encoding='UTF-8'):
            raise CameraError(error)

    def _get_camera_info_windows(self) -> List[Dict[str, str]]:
        """Get camera information for WindowsOS.

        Yields:
            List[Dict[str, str]]:
            Returns the information of all connected cameras as a list of dictionary.
        """
        output = list(filter(None, self.output.decode(encoding='UTF-8').splitlines()))  # Filter null values in the list
        if not output:
            return

        for list_ in list_splitter(original_list=output, delimiter='SystemName'):
            values = {}
            for sub_list in list_:
                values[sub_list.split('=')[0]] = sub_list.split('=')[1]
            yield values

    def _list_cameras_windows(self) -> List[str]:
        """Yields the camera name for WindowsOS.

        Yields:
            Names of the connected cameras.
        """
        for camera in self._get_camera_info_windows():
            yield camera.get('Name')

    def _get_camera_info_darwin(self) -> List[Dict[str, str]]:
        """Get camera information for macOS.

        Returns:
            Dict[str, Dict]:
            Returns the raw XML output as a dictionary.
        """
        output = list(filter(None, self.output.decode(encoding='UTF-8').splitlines()))
        if not output:
            return
        output = [v.strip() for v in output][1:]

        # # Return output as dictionary of dictionaries
        # dict_ = {output[0]: {}}
        # new_list = output[1:]
        # new_dict = {}
        # for o in new_list:
        #     if o.endswith(':'):
        #         dict_[output[0]][o.rstrip(':')] = new_dict
        #     else:
        #         new_dict[o.split(':')[0].strip()] = o.split(':')[1].strip()
        # return dict_

        for list_ in list_splitter(original_list=output, delimiter='Unique ID'):
            values = {}
            for sub_list in list_:
                if sub_list.endswith(':'):
                    values['Name'] = sub_list.rstrip(':')
                else:
                    values[sub_list.split(':')[0]] = sub_list.split(':')[1]
            yield values

    def _list_cameras_darwin(self) -> List[str]:
        """Yields the camera name for macOS.

        Yields:
            List[str]:
            Names of the connected cameras.
        """
        for camera in self._get_camera_info_darwin():
            yield camera.get('Name')

    def get_camera_info(self) -> List[Dict[str, str]]:
        """Gets the yielded camera information as a generator object and returns as a list.

        Returns:
            List[Dict[str]]:
            List of dictionaries.
        """
        if settings.macos:
            return list(self._get_camera_info_darwin())
        return list(self._get_camera_info_windows())

    def list_cameras(self) -> List[str]:
        """List of names of all cameras connected.

        Returns:
            List[str]:
            List of camera names.
        """
        if settings.macos:
            return list(self._list_cameras_darwin())
        return list(self._list_cameras_windows())

    def get_index(self) -> str:
        """Get the index and name of each connected camera.

        Returns:
            str:
            Index and name of cameras as a string.
        """
        return '\n'.join([f"{i}: {c}" for i, c in enumerate(self.list_cameras())])


if __name__ == '__main__':
    print(Camera().get_index())
