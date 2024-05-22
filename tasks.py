"""Invoke tasks for the project"""

from invoke import task


@task
def rundev(cmd):
    """Run the development server with uvicorn."""
    cmd.run("uvicorn src.main:appAPI --port 8000 --reload")


@task
def makemigrations(cmd, message):
    """Generate migrations for the database."""
    cmd.run(f"aerich migrate --name '{message}'")


@task
def migrate(cmd):
    """Apply migrations to the database."""
    cmd.run("aerich upgrade")

@task
def initdb(cmd):
    """Create the database tables."""
    cmd.run("aerich init -t src.config.TORTOISE_ORM")
    cmd.run("aerich init-db")


@task
def runtest(cmd, file=None):
    """Run tests."""
    if file:
        cmd.run(f"pytest src/tests/{file}.py")
    else:
        cmd.run("pytest src/tests")
