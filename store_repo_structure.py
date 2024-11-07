# import os
# import json
# from github import Github
# from pymongo import MongoClient
# # from dotenv import load_dotenv
# import datetime

# # # Load environment variables
# # load_dotenv()
# GITHUB_TOKEN = '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'
# MONGODB_URI = "mongodb+srv://learnlink:learnlink@cluster0.ptp95.mongodb.net/learnlink"

# def fetch_repo_structure(repo_name, owner='dkoradiya'):
#     """
#     Fetch the repository structure for a given repository.
    
#     Args:
#         repo_name (str): Name of the repository
#         owner (str): Owner of the repository
    
#     Returns:
#         dict: Repository structure
#     """
#     g = Github(GITHUB_TOKEN)
#     repo = g.get_repo(f'{owner}/{repo_name}')
#     return process_folder(repo)

# def process_folder(repo, path=''):
#     """
#     Process a folder in the repository and return its structure.
    
#     Args:
#         repo: GitHub repository object
#         path (str): Path within the repository
    
#     Returns:
#         dict: Folder structure
#     """
#     contents = repo.get_contents(path)
#     folder_structure = {
#         'readme': None,
#         'media': [],
#         'assets': []
#     }
    
#     for item in contents:
#         if item.type == 'file':
#             raw_url = item.download_url
#             if item.name.lower() == 'readme.md':
#                 folder_structure['readme'] = raw_url
#             elif item.name.endswith(('.mp4', '.jpg', '.jpeg', '.png')):
#                 folder_structure['media'].append(raw_url)
#             else:
#                 folder_structure['assets'].append(raw_url)
#         elif item.type == 'dir':
#             folder_structure[item.name] = process_folder(repo, item.path)
    
#     return folder_structure

# def store_in_mongodb(repo_name, structure):
#     """
#     Store the repository structure in MongoDB.
    
#     Args:
#         repo_name (str): Name of the repository
#         structure (dict): Repository structure to store
#     """
#     client = MongoClient(MONGODB_URI)
#     db = client['myDatabase']
#     collection = db['repoStructures']
    
#     collection.update_one(
#         {'repo': repo_name},
#         {
#             '$set': {
#                 'structure': structure,
#                 'lastUpdated': datetime.datetime.utcnow()
#             }
#         },
#         upsert=True
#     )
#     print('Repository structure stored successfully')

# def main():
#     g = Github(GITHUB_TOKEN)
#     owner = "dkoradiya"
#     reposname = g.get_repo(f'{owner}/{repo_name}')
#     repo_name = reposname  # Specify your repository name
#     structure = fetch_repo_structure(repo_name)
#     store_in_mongodb(repo_name, structure)

# if __name__ == '__main__':
#     main()







import os
import json
import datetime
import logging
from github import Github
from pymongo import MongoClient

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Environment variables for GitHub token and MongoDB URI
GITHUB_TOKEN = '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'
MONGODB_URI = "mongodb+srv://learnlink:learnlink@cluster0.ptp95.mongodb.net/learnlink"

def fetch_repo_structure(repo, path=''):
    """
    Fetch the structure of the repository (files and directories).
    
    Args:
        repo: GitHub repository object.
        path (str): Path to the current directory in the repository.
    
    Returns:
        dict: The repository's structure.
    """
    contents = repo.get_contents(path)
    folder_structure = {
        'readme': None,
        'media': [],
        'assets': []
    }

    for item in contents:
        if item.type == 'file':
            raw_url = item.download_url
            if item.name.lower() == 'readme.md':
                folder_structure['readme'] = raw_url
            elif item.name.lower().endswith(('.mp4', '.jpg', '.jpeg', '.png')):
                folder_structure['media'].append(raw_url)
            else:
                folder_structure['assets'].append(raw_url)
        elif item.type == 'dir':
            folder_structure[item.name] = fetch_repo_structure(repo, item.path)

    return folder_structure

def store_in_mongodb(repo_name, structure):
    """
    Store the repository structure in MongoDB.
    
    Args:
        repo_name (str): Name of the repository.
        structure (dict): The structure to store.
    """
    try:
        client = MongoClient(MONGODB_URI)
        db = client['myDatabase']
        collection = db['repoStructures']
        
        # Upsert repository structure data
        collection.update_one(
            {'repo': repo_name},
            {
                '$set': {
                    'structure': structure,
                    'lastUpdated': datetime.datetime.utcnow()
                }
            },
            upsert=True
        )
        logging.info(f"Repository structure for '{repo_name}' stored successfully.")
    except Exception as e:
        logging.error(f"Error storing repository structure: {e}")
    finally:
        # Ensure the MongoDB connection is closed after operation
        client.close()

def get_repository(owner='dkoradiya'):
    """
    Get the repository object from GitHub using the current context (authenticated user).
    
    Args:
        owner (str): Owner of the repository (user or organization).
    
    Returns:
        repo: GitHub repository object.
    """
    try:
        g = Github(GITHUB_TOKEN)
        # Get the authenticated user's current repository (repo_name is dynamic)
        repo = g.get_repo(f'{owner}/{get_current_repo_name()}')
        return repo
    except Exception as e:
        logging.error(f"Error fetching repository: {e}")
        return None

def get_current_repo_name():
    """
    Fetch the repository name dynamically from the current GitHub repository.
    
    Returns:
        str: Repository name.
    """
    try:
        g = Github(GITHUB_TOKEN)
        # The authenticated user can get the list of repositories they own or have access to.
        user = g.get_user()
        for repo in user.get_repos():
            if repo.get_contents('.').last_modified:  # Check if this repo contains the current script
                return repo.name
        logging.error("Unable to determine the repository name.")
        return None
    except Exception as e:
        logging.error(f"Error fetching the repository name: {e}")
        return None

def main():
    # The owner of the repo (can be an organization or personal user)
    owner = "dkoradiya"  # Replace with your GitHub username or organization name
    
    # Get the repository object dynamically
    repo = get_repository(owner)
    if repo is None:
        logging.error(f"Repository not found or access denied.")
        return

    # Fetch the repository structure
    structure = fetch_repo_structure(repo)
    
    # Store the structure in MongoDB
    store_in_mongodb(repo.name, structure)

if __name__ == '__main__':
    main()

