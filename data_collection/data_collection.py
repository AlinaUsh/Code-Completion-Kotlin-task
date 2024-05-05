from typing import List, Tuple

from kopyt.kopyt import Parser
from kopyt.kopyt import node

import csv
import os
import git
import json
from tqdm import tqdm

import signal


def timeout_handler(signum, frame):
    raise TimeoutError("Function execution timed out")

signal.signal(signal.SIGALRM, timeout_handler)


def clone_repository(repo_url, destination):
    """
    Clone the GitHub repository to the specified destination.

    Parameters:
        repo_url (str): The URL of the GitHub repository to clone.
        destination (str): The directory where the repository will be cloned.
    """
    git.Repo.clone_from(repo_url, destination)
    print("Cloned")


def collect_files(directory: str, extension: str) -> List[str]:
    """
    Collect files with a specified extension within a directory.

    Parameters:
        directory (str): The path to the directory to search for files.
        extension (str): The file extension to filter files by.
    Returns:
        list: A list of file paths with the specified extension.
    """
    collected_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                collected_files.append(os.path.join(root, file))
    return collected_files


def format_dataset_row(cur_node: node.Node) -> Tuple[str, str, str, str]:
    """
    Format a dataset row from a parsed node.

   Parameters:
       cur_node (node.Node): The parsed node.
       file_num (int): The index of the file being processed.
   Returns:
       tuple: A tuple containing the signature, body, docstring, and identifier.
    """
    if isinstance(cur_node, node.Docstring):
        return (
            cur_node.declaration._declaration(),
            cur_node.declaration.body.__str__(),
            cur_node.docstring.__str__(),
            f"f{file_num}:m{cur_node.position.line}"

        )
    elif isinstance(cur_node, node.FunctionDeclaration):
        return (
            cur_node._declaration(),
            cur_node.body.__str__(),
            "",
            f"f{file_num}:m{cur_node.position.line}"
        )
    return "", "", "", ""


def parse_code(cur_node: node.Node, file_num: int) -> List[Tuple[str, str, str, str]]:
    """
    Recursively parse a node and its children.

    Parameters:
        cur_node (node.Node): The current node to parse.
        file_num (int): The index of the file being processed.
    Returns:
        list: A list of parsed functions.
    """
    if cur_node is None:
        return []
    parsed_functions = []
    if isinstance(cur_node, node.Docstring):
        if isinstance(cur_node.declaration, node.FunctionDeclaration) and cur_node.declaration is not None:
            parsed_functions.append(format_dataset_row(cur_node))
        else:
            parsed_functions += parse_code(cur_node.declaration, file_num)
    if isinstance(cur_node, node.FunctionDeclaration):
        parsed_functions.append(format_dataset_row(cur_node))
    if isinstance(cur_node, (node.ClassDeclaration, node.InterfaceDeclaration, node.ObjectDeclaration)) and \
            cur_node.body is not None:
        for member in cur_node.body.members:
            parsed_functions += parse_code(member, file_num)
    return parsed_functions


def parse_file(code: str, file_num: int) -> List[Tuple[str, str, str, str]]:
    """
    Parse Kotlin code and extract function data.

    Parameters:
        code (str): The Kotlin code to parse.
        file_num (int): The index of the file being processed.
    Returns:
        list: A list of parsed functions.
        """
    parser = Parser(code)
    result = parser.parse()
    parsed_functions = []
    for declaration in result.declarations:
        parsed_functions += parse_code(declaration, file_num)
    return parsed_functions


def append_to_dataset(dataset: str, new_data: List[Tuple[str, str, str, str]]):
    """
    Append new data to an existing dataset.

    Parameters:
        dataset (str): The path to the existing CSV dataset file.
        new_data (list of tuples): The new rows of data to append to the dataset.
    """
    with open(dataset, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(new_data)


if __name__ == '__main__':
    with open('config.json', 'r') as file:
        config = json.load(file)
    clone_repository(config['repository_url'], config['clone_to'])

    header = ['signature', 'body', 'docstring', 'id']
    output_file = config['dataset_name']

    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)

    files = collect_files(config['clone_to'], '.kt')
    failed_to_parse_files = []

    for file_num, file in enumerate(tqdm(files)):
        signal.alarm(15)
        try:
            with open(file, 'r') as f:
                code = "\n".join(f.readlines())
            parsed_data = parse_file(code, file_num)
            append_to_dataset(output_file, parsed_data)
        except Exception as e:
            failed_to_parse_files.append(file)
        signal.alarm(0)

    all = len(files)
    success = all - len(failed_to_parse_files)
    print(
        f"Successfully parsed {success}/{all} files | {'{:0.2f}'.format(success / all * 100)}%"
    )
