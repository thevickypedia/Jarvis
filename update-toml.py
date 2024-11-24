import sys

import toml


def update_name_in_pyproject(file_path, project_name):
    """Update project name handler in pyproject.toml.

    Args:
        file_path: Source filepath.
        project_name: New project name.
    """
    try:
        with open(file_path, "r") as file:
            data = toml.load(file)
    except FileNotFoundError:
        print(f"TOML file {file_path!r} not found!")
        return

    # Update the 'name' in the '[project]' section
    if "project" in data:
        data["project"]["name"] = project_name
        print(f"Updated 'name' to {project_name!r} in [project]")
    else:
        print("[project] section not found in TOML file!")
        return

    # Write the updated content back to the TOML file
    with open(file_path, "w") as file:
        toml.dump(data, file)


if __name__ == "__main__":
    update_name_in_pyproject(sys.argv[1], sys.argv[2])
