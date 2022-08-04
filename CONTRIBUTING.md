# Contributing

Contributions to Timed backend are very welcome! Best have a look at the open [issues](https://github.com/adfinis/timed-backend)
and open a [GitHub pull request](https://github.com/adfinis/timed-backend/compare). See instructions below how to setup development
environment. Before writing any code, best discuss your proposed change in a GitHub issue to see if the proposed change makes sense for the project.

## Setup development environment

### Clone

To work on Timed backend you first need to clone

```bash
git clone https://github.com/adfinis/timed-backend.git
cd timed-backend
```

### Open Shell

Once it is cloned you can easily open a shell in the docker container to
open a development environment.

```bash
make shell
```

### Testing

Once you have shelled in to the docker container as described above
you can use common python tooling for formatting, linting, testing
etc.

```bash
# linting
flake8
# format code
black .
# running tests
pytest
# create migrations
./manage.py makemigrations
```

Writing of code can still happen outside the docker container of course.

### Install new requirements

In case you're adding new requirements you simply need to build the docker container
again for them to be installed and re-open shell.

```bash
docker-compose build --pull
```

### Setup pre commit

Pre commit hooks are an additional option instead of executing checks in your editor of choice.

First create a virtualenv with the tool of your choice before running below commands:

```bash
pip install pre-commit
pip install -r requiements-dev.txt -U
pre-commit install
```
