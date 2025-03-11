[![Run Tests](https://github.com/codegreen-framework/codegreen-core/actions/workflows/test.yml/badge.svg)](https://github.com/codegreen-framework/codegreen-core/actions/workflows/test.yml) [![Publish to PyPI](https://github.com/codegreen-framework/codegreen-core/actions/workflows/workflow.yml/badge.svg)](https://github.com/codegreen-framework/codegreen-core/actions/workflows/workflow.yml)

This repository contains the main functionality of the codegreen project. The complete documentation including installation and usage are available on the [documentation website](https://codegreen-framework.github.io/codegreen-core/). 

# Development 

## Installation
- `git clone`
- install poetry
- install in editable mode : `poetry install`

## Github workflows
Changes in the repo also triggers github actions 

## Development workflow 
- the `release` branch contains the latest stable version of the released python package 
- the `main` branch contains stable, tested code ready to be released. 
- the `dev` branch is the main working branch. All feature branches are merged to `dev` 

### Releasing  the package
- Ensure new changes are merged to `dev` and the version number is bumped according to [sematic versioning](https://semver.org/).
-  Merge `dev`to `main`. This should trigger tests.
-  Create a git tag for the new version :
```
git checkout main
git pull
git tag vX.Y.Z  # Replace X.Y.Z with the new version number
git push origin vX.Y.Z
```
- Create a PR from `main` to `release` and get one approval
- Once the PR is merged, it will trigger the release of the new package version and publish the documentation.