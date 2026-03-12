# Contributing Guide

Guidelines for contributing to the Alfred AI Assistant project.

---

## Welcome! 👋

We appreciate your interest in contributing to Alfred. This guide explains how to contribute effectively.

---

## Code of Conduct

- **Be respectful**: Treat everyone with professionalism
- **Be constructive**: Focus on improving the project
- **Be collaborative**: Work together to solve problems
- **Be honest**: Report issues transparently

Report violations to: conduct@locle.dev

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/alfred-ai-assistant.git
cd alfred-ai-assistant
```

### 2. Create Branch

```bash
# Feature branch
git checkout -b feature/my-feature

# Bugfix branch
git checkout -b bugfix/issue-description

# Docs branch
git checkout -b docs/update-guide

# Branch naming convention: {type}/{description}
# Types: feature, bugfix, docs, refactor, test, chore
```

### 3. Set Up Development Environment

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r src/requirements.txt -r requirements-dev.txt

# Verify setup
make verify
```

---

## Making Changes

### Code Style

Alfred follows **PEP 8** with Black formatting.

```bash
# Format code (automatically)
make format
# or
black src/

# Check linting
make lint
# or
pylint src/

# Type checking
make type-check
# or
mypy src/
```

### Code Examples

**Good practice** ✓:

```python
def process_question(question: str) -> str:
    """Process a user question and return a response.

    Args:
        question: User input question string

    Returns:
        Assistant response string

    Raises:
        InvalidQuestionError: If question is invalid
    """
    if not question:
        raise InvalidQuestionError("Question cannot be empty")

    return response
```

**Avoid** ✗:

```python
def process(q):  # No type hints, unclear name
    # Process the question
    if q == "":
        return None  # No exception
    return resp  # Undefined variable
```

### Documentation

- Write clear docstrings (Google style)
- Include inline comments for complex logic
- Update relevant docs when changing behavior
- Link to related issues/PRs

### Tests

Every change should include tests.

```python
# tests/unit/test_my_feature.py
import pytest
from src.my_module import my_function

def test_my_function_success():
    """Test happy path."""
    result = my_function("input")
    assert result == "expected"

def test_my_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        my_function("")
```

Run tests:

```bash
make test           # All tests
pytest -v           # Verbose
pytest -k my_test   # Specific test
pytest --cov=src    # With coverage
```

**Target**: 80%+ code coverage

---

## Commit Messages

Use clear, descriptive commit messages.

### Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation change
- **style**: Code style (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without behavior change
- **test**: Adding/updating tests
- **chore**: Build, dependencies, tooling changes

### Examples

```bash
git commit -m "feat: add knowledge base versioning"
git commit -m "fix: handle null responses from Bedrock"
git commit -m "docs: update deployment guide"
git commit -m "test: improve coverage for rate limiting"
git commit -m "refactor: simplify response caching logic"
```

---

## Pull Request Process

### 1. Push Your Branch

```bash
git push origin feature/my-feature
```

### 2. Create PR on GitHub

- **Title**: Clear, descriptive (follows commit message format)
- **Description**: Explains what and why
- **References**: Link related issues (#123)

### PR Description Template

```markdown
## Description

Brief explanation of changes.

## Related Issues

Closes #123
Related to #456

## Changes

- Change 1
- Change 2
- Change 3

## Testing

How to test these changes?

## Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
```

### 3. Code Review

- Address reviewer feedback
- Push changes (don't force-push)
- Re-request review after changes
- Be respectful and collaborative

### 4. Merge

Once approved:

```bash
# Maintainer merges PR
# Squash commits for cleaner history
```

---

## Types of Contributions

### Bug Reports

**Report bugs on GitHub Issues**

Include:

- Clear title
- Description of problem
- Steps to reproduce
- Expected vs actual behavior
- Environment (dev/staging/prod)
- Logs/screenshots
- Your environment details

### Feature Requests

**Suggest features on GitHub Discussions or Issues**

Include:

- Problem being solved
- Proposed solution
- Alternative solutions considered
- Examples (if applicable)
- Estimated complexity (low/medium/high)

### Documentation

- Fix typos and clarity
- Add examples
- Update outdated information
- Add troubleshooting guides

### Code

- Bug fixes
- Performance improvements
- New features
- Refactoring for clarity

### Testing

- Improve test coverage
- Add integration tests
- Test edge cases
- Performance tests

---

## Areas for Contribution

### High Priority

- [ ] Bedrock model comparison (cost vs quality)
- [ ] Enhanced caching strategies
- [ ] Performance optimization
- [ ] Security improvements
- [ ] Monitoring/observability

### Medium Priority

- [ ] Additional error handling
- [ ] Documentation improvements
- [ ] CI/CD enhancements
- [ ] Infrastructure improvements
- [ ] Developer experience

### Low Priority

- [ ] Code style improvements
- [ ] Comment clarity
- [ ] Minor optimizations
- [ ] Dependency updates

---

## Development Workflow Example

### Scenario: Add New Feature

```bash
# 1. Create branch
git checkout -b feature/add-conversation-history

# 2. Make changes
vim src/agents/assistant_agent.py
vim src/repositories/conversation_repository.py

# 3. Add tests
vim tests/unit/test_conversation_history.py

# 4. Format and lint
make format
make check

# 5. Run tests
make test

# 6. Commit
git add .
git commit -m "feat: add conversation history tracking"

# 7. Push
git push origin feature/add-conversation-history

# 8. Create PR on GitHub
# (GitHub will show button to create PR)

# 9. Address feedback
# (make changes, push again - no force-push!)

# 10. Merge (maintainer)
```

---

## Local Testing

### Before Submitting PR

```bash
# Run all checks
make check      # lint + format + type-check

# Run all tests
make test       # with coverage report

# Build Lambda package
make build

# Test locally (if applicable)
sam local start-api    # Test locally
curl http://localhost:3000/chat ...
```

### Testing Against AWS

```bash
# Deploy to staging
terraform -chdir=terraform apply -var-file=staging.tfvars

# Run smoke tests
make test-staging

# Monitor logs
aws logs tail /aws/lambda/alfred-assistant-handler --follow
```

---

## Performance Considerations

- Don't add heavy dependencies unnecessarily
- Consider Lambda cold start impact
- Cache expensive operations
- Be mindful of Bedrock token usage
- Profile before optimizing

---

## Security Guidelines

- **Never commit secrets** (use .env, rotate regularly)
- **Validate all inputs**
- **Use least privilege** (IAM permissions)
- **Report security issues privately** → security@locle.dev
- **Keep dependencies updated**

---

## Performance Expectations

### Response Time

- Acknowledge PR within 24 hours
- Reviews completed within 2-3 days
- Minor fixes faster, major features may take longer

### Approval

Your PR needs:

- **Approval** from at least 1 maintainer
- **Green checks** on CI (tests, lints, etc.)
- **Updated documentation** (if applicable)

---

## Questions or Concerns?

- **GitHub Discussions**: Ask in discussions tab
- **Email**: team@locle.dev
- **Slack**: #alfred-development channel
- **Issues**: Check existing issues before asking

---

## Maintainers

- **Loc Le**: @locle (core architecture, deployment)

---

## Recognition

Contributors will be recognized in:

- [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Release notes
- Project README

---

## Standards & Guidelines

### Python Standards

- Python 3.12+
- PEP 8 style guide
- Type hints required (mypy checks)
- Docstrings required (Google style)
- 80%+ test coverage

### Infrastructure Standards

- Infrastructure-as-Code (Terraform)
- Documented variables and outputs
- Cost-efficient configurations
- Security best practices

### Documentation Standards

- Clear and concise
- Examples provided
- Up-to-date
- Searchable (good headings)

---

## Additional Resources

- [Development Guide](DEVELOPMENT.md): Local setup and workflow
- [Architecture Overview](ARCHITECTURE.md): System design
- [API Documentation](API.md): API specification
- [Deployment Guide](DEPLOYMENT.md): Infrastructure and deployment

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Thank You! 🙏

We're grateful for your interest in improving Alfred. Your contributions help make this project better for everyone!

---

**Happy coding! 🚀**
