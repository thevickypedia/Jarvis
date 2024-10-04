import sys

import toml


def update_name_in_pyproject(file_path, new_name_value):
    try:
        with open(file_path, 'r') as file:
            data = toml.load(file)
    except FileNotFoundError:
        print(f"TOML file {file_path!r} not found!")
        return

    # Update the 'name' in the '[project]' section
    if 'project' in data:
        data['project']['name'] = new_name_value
        print(f"Updated 'name' to {new_name_value!r} in [project]")
    else:
        print("[project] section not found in TOML file!")
        return

    # Write the updated content back to the TOML file
    with open(file_path, 'w') as file:
        toml.dump(data, file)
        file.flush()


if __name__ == "__main__":
    update_name_in_pyproject(sys.argv[1], sys.argv[2])
