# NotebookLM Wizard Agent 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Rich](https://img.shields.io/badge/built%20with-Rich-green.svg)](https://github.com/Textualize/rich)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/xlastfire/notebooklm/graphs/commit-activity)

A powerful, multi-account CLI agent for **NotebookLM** that automates research, source management, and artifact generation with a professional wizard interface. Built for power users who need to manage complex research workflows across multiple Google accounts.

## ✨ Key Features

- **Multi-Account Support**: Switch between multiple Google accounts seamlessly using local JSON storage.
- **Background Tasks**: Long-running operations (Deep Research, Artifact Generation, Uploads) run in the background, allowing you to continue using the CLI.
- **Auto-Pilot Mode**: One-click pipeline to create a notebook, perform research, and generate a downloadable podcast (Audio Overview).
- **Deep Research**: High-quality automated web research and source importing.
- **Artifact Management**: Generate and download Quizzes, Study Guides, Mind Maps, Audio Overviews, and more in any target language.
- **Native Sinhala Support**: Specialized defaults for Sinhala ("si") language output and artifact generation.
- **Session Persistence**: Built-in `keepalive` mechanism that automatically rotates Google cookies to prevent session timeouts during long-running tasks.
- **Windows Optimized**: Fixed common asyncio hangs on Windows using `WindowsSelectorEventLoopPolicy`.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/xlastfire/notebooklm.git
   cd notebooklm
   ```

2. **Install dependencies**:
   ```bash
   pip install notebooklm-py rich
   ```

3. **Set environment variables** (Recommended for Windows):
   ```powershell
   $env:PYTHONUTF8=1
   ```

## 🔐 Account Setup

To use the agent, you need to provide your NotebookLM session cookies in a JSON file inside the `accounts/` folder.

### JSON Structure
Each account file (e.g., `accounts/my_account.json`) must follow this structure:

```json
{
  "cookies": [
    {
      "name": "__Secure-1PSID",
      "value": "...",
      "domain": ".google.com",
      "path": "/",
      "secure": true,
      "httpOnly": true
    },
    ...
  ],
  "origins": []
}
```

> [!TIP]
> You can obtain this JSON by using a browser extension like "EditThisCookie" or "Cookie-Editor" while logged into NotebookLM. Export the cookies in JSON format and wrap them in the structure above.

## 🚀 Usage

Run the agent with:
```bash
python main.py
```

### Workflow:
1. **Select Account**: Choose from the JSON files found in your `accounts/` directory.
2. **Select Notebook**: Pick an existing notebook or create a new one.
3. **Actions**:
   - **Chat**: Interactive Q&A with your sources.
   - **Manage Sources**: Add URLs, PDF files, or text snippets in the background.
   - **Research**: Start a Fast or Deep research task.
   - **Artifacts**: Generate AI content and download it once ready.
   - **Auto-Pilot**: Fully automate the transition from a "Topic" to a "Downloadable Podcast".

## 🏗️ Architecture

- `main.py`: Entry point with Windows compatibility fixes and global error handling.
- `menu_agent.py`: The Rich-powered CLI UI logic, handling menus and asynchronous background task state.
- `client_wrapper.py`: A robust wrapper around the `notebooklm-py` library, implementing background task tracking, snapshotting, and notifications.

## 🤝 Contributing

Contributions are welcome! Whether it's fixing bugs, adding new features, or improving documentation, feel free to open a Pull Request or Issue. I am looking for help to make this agent even more powerful.

## 🙏 Acknowledgements

A huge thank you to [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py) for providing the incredible core library that makes this agent possible.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

