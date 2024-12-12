import os

import toml

FILE_PATH = os.environ.get("FILE_PATH", "pyproject.toml")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "jarvis-ironman")


def update_name_in_pyproject() -> None:
    """Update project name handler in metadata."""
    with open(FILE_PATH) as file:
        data = toml.load(file)

    # Update the 'name' in the '[project]' section
    data["project"]["name"] = PROJECT_NAME

    # Write the updated content back to the TOML file
    with open(FILE_PATH, "w") as file:
        toml.dump(data, file)
        file.flush()

    print(f"Updated 'name' to {PROJECT_NAME!r} in [project]")


if __name__ == "__main__":
    update_name_in_pyproject()
