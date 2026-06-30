# Contributing to BulletLab

Thank you for your interest in contributing to BulletLab! Every contribution — whether it's a bug report, a new example, improved documentation, or a code change — helps make the framework better for everyone.

---

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

---

## Ways to Contribute

| Contribution type | Where to start |
|---|---|
| Bug reports | [Open an Issue](https://github.com/NuclearVenom/BulletLab/issues/new?template=bug_report.md) |
| Feature requests | [Open an Issue](https://github.com/NuclearVenom/BulletLab/issues/new?template=feature_request.md) |
| Code contributions | Fork → branch → PR |
| Documentation | Edit Markdown under `docs/` |
| New examples | Add a file under `examples/` |
| Discussions | [GitHub Discussions](https://github.com/NuclearVenom/BulletLab/discussions) |

---

## Reporting Bugs

Before opening a bug report, please search existing issues to avoid duplicates.

When reporting a bug, include:

- **BulletLab version** (`pip show bulletlab`)
- **Python version** (`python --version`)
- **Operating system and version**
- **Minimal reproducible example** — the smallest code that demonstrates the problem
- **Full error traceback**
- **Expected vs actual behavior**

Use the bug report issue template when available.

---

## Suggesting Features

Feature requests are welcome. Please:

1. Check the [Roadmap](ROADMAP.md) — your idea may already be planned.
2. Search existing issues and discussions.
3. Open a new issue with a clear description of the feature and its motivation.
4. Describe how it fits within BulletLab's design philosophy (clean API, PyBullet abstraction, research-oriented).

---

## Documentation Contributions

Documentation lives under `docs/`. The site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

- Fix typos, clarify descriptions, or improve code examples in any `.md` file.
- To add a new guide, create a file under `docs/guides/` and register it in `mkdocs.yml`.
- Follow the existing documentation style (active voice, short paragraphs, runnable code examples).

---

## Example Contributions

Examples live under `examples/`. Good examples:

- Are **self-contained** and runnable with a single `python examples/your_example.py`.
- Include a module-level docstring explaining what the example demonstrates.
- Use **BulletLab's high-level API** — avoid raw `pybullet` calls unless absolutely necessary.
- Follow the existing naming convention: `NN_descriptive_name.py`.

---

## Development Setup

### Prerequisites

- Python 3.10+
- A working C++ build environment (required by PyBullet)

### Clone and install in editable mode

```bash
git clone https://github.com/NuclearVenom/BulletLab.git
cd BulletLab
pip install -e ".[dev]"
```

The `[dev]` extra installs testing and documentation dependencies.

---

## Running Examples

```bash
python examples/01_differential_drive_rover.py
python examples/04_drone_parameter_tuning.py
```

---

## Running Tests

```bash
pytest tests/ -v --cov=bulletlab --cov-report=term-missing
```

All tests must pass before a PR can be merged. New features should include corresponding tests.

---

## Building Documentation Locally

```bash
mkdocs serve
```

Then open `http://127.0.0.1:8000` in your browser. The site hot-reloads on file changes.

---

## Commit Message Style

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

| Prefix | Use for |
|---|---|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | Documentation changes only |
| `refactor:` | Code changes with no new features or bug fixes |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance tasks (version bumps, CI, build) |
| `perf:` | Performance improvements |

**Examples:**

```
feat: add World.load_heightfield for procedural terrain generation
fix: correct joint velocity sign convention in differential drive
docs: add external forces section to robot_guide.md
refactor: extract quaternion math into math_utils module
test: add unit tests for Robot.apply_force
```

Keep the subject line under 72 characters. Use the body to explain *why* the change was made, not just *what*.

---

## Pull Request Checklist

Before submitting a PR, confirm all of the following:

- [ ] The code works and all existing tests pass (`pytest tests/`)
- [ ] New functionality includes tests where practical
- [ ] Public APIs include complete docstrings (Args, Returns, Example)
- [ ] Documentation is updated if the PR changes user-facing behavior
- [ ] The example in `examples/` is updated if the PR affects the API it demonstrates
- [ ] Commit messages follow the Conventional Commits style
- [ ] The PR description clearly explains the motivation and approach
- [ ] Backward compatibility is preserved (or breaking changes are explicitly noted)

---

## Coding Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Use type annotations for all public functions and methods.
- Use Google-style docstrings (the project uses `mkdocstrings` with the Google handler).
- Prefer explicit names over abbreviations.
- Keep public APIs minimal — it is easier to add than to remove.
- Preserve API consistency: new methods should feel at home next to existing ones.
- Maintain backward compatibility whenever practical. Breaking changes require a clear justification and a version bump.

---

## Documentation Style

- Write in the **second person** ("you can...") for guides and tutorials.
- Use **active voice** ("call `robot.reset()`" not "`robot.reset()` should be called").
- Every public method should have a runnable `Example::` docstring block.
- Code examples in Markdown use `python` fenced blocks.
- Keep prose concise — prefer a table or list over a paragraph when presenting multiple options.

---

## Review Process

1. Open a PR against the `main` branch.
2. A maintainer will review the PR, leave comments, and request changes if needed.
3. Once approved, the maintainer will merge the PR.
4. Please respond to review comments within a reasonable timeframe.

We aim to review all PRs within a week. Complex changes may take longer.

Thank you again for contributing to BulletLab!
