"""Invoke tasks for the project"""

from invoke import task


@task
def rundev(cmd):
    """Run the development server with uvicorn."""
    cmd.run("uvicorn src.main:appAPI --port 8000 --reload")


@task
def runtest(cmd, file=None):
    """Run tests."""
    if file:
        cmd.run(f"pytest src/tests/{file}.py")
    else:
        cmd.run("pytest src/tests")
