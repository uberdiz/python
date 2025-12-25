"""
Summarizer Agent - Fixed function signature
"""

def summarizer_agent(project_path, api_url, model, api_provider="openai", token=None):
    """Generate project documentation - FIXED SIGNATURE"""
    import os
    
    project_name = os.path.basename(project_path)
    
    files_updated = []
    
    # Update README.md
    readme_path = os.path.join(project_path, "README.md")
    readme_content = f"""# {project_name}

## Project Overview

This project was developed using AI Dev IDE - an intelligent development environment with AI assistance.

## Features

- AI-assisted code generation
- Automated testing
- Code review and optimization
- Project planning
- GitHub integration

## Structure

- `main.py`: Main application entry point
- `utils.py`: Utility functions
- `tests/`: Test files
- `requirements.txt`: Project dependencies

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## AI Dev IDE

This project was created and enhanced using AI Dev IDE's intelligent coding assistant.
"""

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    files_updated.append("README.md")
    
    # Update PORTFOLIO.md
    portfolio_path = os.path.join(project_path, "PORTFOLIO.md")
    portfolio_content = f"""# {project_name} - Portfolio

## 📋 Project Details

**Type**: Python Application
**Status**: ✅ Active
**Complexity**: ⭐⭐⭐
**AI Assistance**: Yes (AI Dev IDE)

## 🎯 Purpose

Project developed with AI assistance to demonstrate modern Python development practices.

## 🛠️ Technologies

- Python 3.8+
- AI-assisted development tools
- Automated testing framework
- Version control integration

## 📈 Learning Outcomes

1. **AI-Assisted Development**: Using AI to generate and optimize code
2. **Testing**: Implementing comprehensive test suites
3. **Documentation**: Creating clear, maintainable documentation
4. **Project Management**: Structured project planning and execution

## 🏆 Achievements

✅ Complete project setup
✅ AI-generated code implementation
✅ Automated testing
✅ Comprehensive documentation
✅ Version control integration

## 🔮 Future Enhancements

Potential improvements and features to add in future iterations.

---

*Created with AI Dev IDE - The intelligent development environment*
"""

    with open(portfolio_path, "w", encoding="utf-8") as f:
        f.write(portfolio_content)
    files_updated.append("PORTFOLIO.md")
    
    return files_updated
