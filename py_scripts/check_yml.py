import yaml
import re
import os
import pipreqs
import tempfile
from pip._internal.network.session import PipSession
from pip._internal.index.package_finder import PackageFinder
from pip._internal.models.search_scope import SearchScope
from pip._internal.req.constructors import install_req_from_line

def extract_python_packages(yaml_file):
    """
    Provided a .yml file, extracts the packages
    """
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"File {yaml_file} not found.")
        return []
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return []

    packages = []
    for dep in data['dependencies']:
        if isinstance(dep, str):
            if '=' in dep:
                pkg = dep.split('=')[0]
                packages.append(pkg)
            else:
                packages.append(dep)
        elif isinstance(dep, dict) and 'pip' in dep:
            packages.extend(dep['pip'])

    return packages

def check_packages_on_pypi(packages):
    """
    Checks which packages are available on pypi, to exclude conda specific packages
    """
    available_packages = []
    session = PipSession()
    search_scope = SearchScope([], [])
    finder = PackageFinder(search_scope=search_scope, session=session)

    for package in packages:
        req = install_req_from_line(package)
        if finder.find_requirement(req, upgrade=False):
            available_packages.append(package)
        else:
            print(f"Package {package} not found on PyPI.")

    return available_packages

def find_used_packages(directories):
    """
    Finds which packages are actually used in the project
    """
    with tempfile.TemporaryDirectory() as tempdir:
        for directory in directories:
            pipreqs.init({'<directory>': directory, 'savepath': os.path.join(tempdir, 'requirements.txt')})

        requirements_file = os.path.join(tempdir, 'requirements.txt')
        used_packages = []

        with open(requirements_file, 'r') as file:
            used_packages = [line.strip().split('==')[0] for line in file.readlines()]

    return used_packages

def generate_requirements_txt(available_packages, used_packages):
    """
    Generates the requirements.txt file to use with pip
    """
    final_packages = set(available_packages).intersection(set(used_packages))
    with open('requirements.txt', 'w') as file:
        for package in final_packages:
            file.write(f"{package}\n")

def main():
    yaml_file = 'environment.yml'  # to do: args
    code_dirs = ['src', 'notebooks']  # to do: extract from main path

    # Extract packages from YAML
    extracted_packages = extract_python_packages(yaml_file)
    print(f"Extracted packages: {extracted_packages}")

    # Check which are available on PyPI
    available_packages = check_packages_on_pypi(extracted_packages)
    print(f"Available packages: {available_packages}")

    # Find used packages in the codebase
    used_packages = find_used_packages(code_dirs)
    print(f"Used packages: {used_packages}")

    # Generate requirements.txt
    generate_requirements_txt(available_packages, used_packages)
    print("requirements.txt file generated.")

if __name__ == "__main__":
    main()
