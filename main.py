import os
import git
from itertools import chain
import datetime
from argparse import ArgumentParser

def list_sub_dirs(path: str, levels: int = 1) -> list:
    entries = map(lambda x: os.path.join(path, x), os.listdir(path))
    sub_dirs = list(filter(lambda x: os.path.isdir(x), entries))
    if levels > 1:
        second_level = map(lambda s: list_sub_dirs(s, levels=levels-1), sub_dirs)
        second_level = list(chain.from_iterable(second_level))
        sub_dirs += second_level
    return sub_dirs

def list_git_repos(path: str) -> list[git.Repo]:
    sub_dirs = list_sub_dirs(path, levels=2)
    repos = []
    git_dirs = set()
    for sub_dir in sub_dirs:
        try:
            repo = git.Repo(sub_dir)
            git_dir = repo.git_dir
            if git_dir not in git_dirs:
                repos.append(repo)
            git_dirs.add(git_dir)
        except git.exc.InvalidGitRepositoryError:
            continue
    return repos

def save_file(content, filename: str):
    with open(filename, "w") as f:
        f.write(content)

def generate_daily_notes(path: str):
    repos = list_git_repos(path)

    lines = [f"# Daily Notes {datetime.date.today()}"]
    repo_count = 0
    commit_count = 0

    for repo in repos:
        author = repo.config_reader().get_value("user", "name")
        commits = repo.iter_commits('--all', max_count=100, since='1.days.ago', author=author)
        commits = filter(lambda x: "Merge pull request" not in x.message and "Merge branch" not in x.message, commits)
        commits = sorted(commits, key=lambda x: x.message)

        if len(commits) == 0:
            continue
        
        repo_name = repo.working_tree_dir.split("/")[-1]
        lines.append(f"## {repo_name}")
        
        for commit in commits:
            lines.append(f"* {commit.message}")
        repo_count += 1
        commit_count += len(commits)
        
    filename = f"daily-notes-{datetime.date.today()}.md"
    
    content = "\n".join(lines)
    save_file(content, filename)
    
    os.system("open " + filename)
    
    print(f"Found {commit_count} commits in {repo_count} repos")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--path", required=True, help="Path to repositories")

    args = parser.parse_args()

    generate_daily_notes(args.path)
    