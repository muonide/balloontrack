# Contributing to GPS Web Tracker

We welcome contributions to the GPS Web Tracker project! This document provides guidelines for contributing.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/gps-web-tracker.git
   cd gps-web-tracker
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\Activate.ps1  # Windows
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🐛 Reporting Issues

Before submitting an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue template** if available
3. **Provide detailed information**:
   - Operating system and version
   - Python version
   - GPS tracker hardware/software details
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Relevant log output

## 💻 Development Guidelines

### Code Style
- Follow **PEP 8** Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Testing
- Write tests for new features
- Ensure existing tests pass
- Test on multiple platforms if possible
- Include both unit tests and integration tests

### Documentation
- Update README.md for significant changes
- Add inline code comments for complex logic
- Update API documentation for new endpoints
- Include examples in docstrings

## 🔧 Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow the coding standards
   - Add/update tests as needed
   - Update documentation

3. **Test your changes**:
   ```bash
   python gps_web_tracker.py  # Basic functionality test
   python cli.py --check-config  # Configuration validation
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear, descriptive title
   - Explain what changes you made and why
   - Reference any related issues
   - Include screenshots for UI changes

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows the project style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No merge conflicts with main branch
- [ ] PR has a clear description

### PR Review Process
1. **Automated checks** will run (if configured)
2. **Code review** by maintainers
3. **Address feedback** if requested
4. **Merge** once approved

## 🎯 Areas for Contribution

### High Priority
- **Error handling improvements**
- **Performance optimizations**
- **Mobile responsiveness enhancements**
- **Additional GPS protocol support**
- **Unit test coverage**

### Medium Priority
- **UI/UX improvements**
- **Configuration management**
- **Logging enhancements**
- **Docker containerization**
- **API rate limiting**

### Low Priority
- **Additional map tile providers**
- **Export functionality**
- **Historical data analysis**
- **Email notifications**
- **Multi-language support**

## 🏗️ Project Structure

```
gps-web-tracker/
├── gps_web_tracker.py      # Main application
├── config.py               # Configuration management
├── cli.py                  # Command line interface
├── templates/              # HTML templates
│   └── index.html
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── CONTRIBUTING.md        # This file
├── LICENSE                # License information
└── .github/               # GitHub specific files
    └── copilot-instructions.md
```

## 🤝 Code of Conduct

- **Be respectful** and professional
- **Focus on the code**, not the person
- **Accept constructive feedback** gracefully
- **Help others** when you can
- **Keep discussions** on-topic

## 📞 Getting Help

- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the README.md first

## 🎉 Recognition

Contributors will be:
- **Listed** in the project contributors
- **Credited** in release notes for significant contributions
- **Acknowledged** in the project documentation

Thank you for contributing to GPS Web Tracker! 🚀
