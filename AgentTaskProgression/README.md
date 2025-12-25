# AI Dev IDE - A Comprehensive Development Environment for Artificial Intelligence

## Project Description

**AI Dev IDE (Integrated Development Environment)** is a cutting-edge software tool designed to streamline and enhance the development process for artificial intelligence applications. This IDE provides a comprehensive set of features that cater to various stages of the AI application lifecycle, from planning and coding through testing and deployment.

## Features

1. **Multi-Agent Pipeline**: The AI Dev IDE is equipped with a multi-agent pipeline that includes Planning, Coding, Reviewing, Testing, and Done agents. This allows for an enhanced workflow where tasks are automatically assigned to the most appropriate agent based on their role in the development process.

2. **Code Generation**: Leveraging advanced language models like Hugging Face's Qwen/Qwen2.5-Coder-7B-Instruct, the Coder Agent generates high-quality code based on provided prompts and plans. This not only accelerates the coding phase but also ensures that generated code is aligned with project requirements.

3. **Error Fixing**: The Fixer Agent uses advanced techniques to iteratively fix errors in code files. It employs language models to understand and correct issues, ensuring that the application remains stable and functional throughout development.

4. **Testing Integration**: Built-in support for iterative testing ensures that every change is rigorously tested before moving on to the next phase. This reduces the risk of introducing bugs into the final product and accelerates the overall development process.

5. **Settings Integration**: The IDE seamlessly integrates with a settings module, allowing users to customize their development environment according to personal preferences or project-specific requirements. Settings include language preferences, editor configurations, and more.

6. **Cross-Platform Compatibility**: Developed using Python and leveraging the Tkinter library for the GUI, the AI Dev IDE is designed to run on a wide range of platforms including Windows, macOS, and Linux, ensuring broad accessibility for developers.

## Setup Instructions

### Prerequisites

Before setting up the AI Dev IDE, ensure you have the following installed:
- Python 3.7 or later
- Pip (Python package installer)
- PyInstaller (for packaging the application)
- CUDA and cuDNN if using GPU acceleration for local inference

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-dev-ide.git
   cd ai-dev-ide
   ```

2. **Create a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Build the Application** (for standalone executable):
   ```bash
   pyinstaller --onefile app.py  # For Windows
   PyInstaller.__main__.py build_exe.py  # For macOS/Linux
   ```

5. **Run the Application**:
   ```bash
   python launcher.py  # For development mode
   ./dist/AIDevIDE  # For standalone executable
   ```

## Usage

1. **Launch the IDE** from the command line or through the desktop shortcut.
2. Use the integrated terminal to run and debug your code.
3. Utilize the GUI for task management, settings adjustments, and real-time feedback on development processes.

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](https://github.com/yourusername/ai-dev-ide/blob/main/CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## Support

For support, please open an issue in the GitHub repository or contact the project maintainers directly.

---

Thank you for your interest in the AI Dev IDE! We hope this tool empowers you and your team to develop sophisticated AI applications more efficiently and effectively.