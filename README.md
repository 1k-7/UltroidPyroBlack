<p align="center">
  <img src="./resources/extras/logo_readme.jpg" alt="TeamUltroid Logo" width="200">
</p>
<h1 align="center">
  <b>Ultroid - The Next-Gen Telegram UserBot</b>
</h1>

<p align="center">
  <b>A powerful, stable, and pluggable Telegram userbot with Voice & Video Call music features, built on the robust Telethon library.</b>
</p>

<p align="center">
  <a href="https://github.com/TeamUltroid/Ultroid/releases/latest"><img src="https://img.shields.io/badge/Ultroid-v0.8-crimson" alt="Version"></a>
  <a href="https://github.com/TeamUltroid/Ultroid/stargazers"><img src="https://img.shields.io/github/stars/TeamUltroid/Ultroid?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/TeamUltroid/Ultroid/fork"><img src="https://img.shields.io/github/forks/TeamUltroid/Ultroid?style=flat-square&color=orange" alt="Forks"></a>
  <a href="https://github.com/TeamUltroid/Ultroid/graphs/contributors"><img src="https://img.shields.io/github/contributors/TeamUltroid/Ultroid?style=flat-square&color=green" alt="Contributors"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-v3.10.3-blue" alt="Python"></a>
  <a href="https://github.com/TeamUltroid/Ultroid/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-AGPL-blue" alt="License"></a>
  <a href="https://makeapullrequest.com"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome"></a>
</p>

---

## 🚀 What is Ultroid?

Ultroid is a feature-rich Telegram userbot that enhances your Telegram experience. With a focus on stability and extensibility, Ultroid offers a wide range of features, from playing music in voice calls to powerful plugins.

---

## ✨ Features

-   **🎵 Music Bot:** Play your favorite tunes in voice and video calls.
-   **🔌 Pluggable:** Extend Ultroid's functionality with a rich ecosystem of plugins.
-   **🚀 Fast & Stable:** Built on the asynchronous Telethon library for maximum performance.
-   **☁️ Multiple Deployment Options:** Deploy on Heroku, Okteto, or your own machine with ease.
-   **🤝 Active Community:** Join our friendly community for support and development discussions.

---

##  deployment

You can deploy Ultroid in several ways. Choose the one that suits you best.

### Method 1: Deploy to Heroku

The easiest way to get started. Just click the button below and follow the on-screen instructions.

<a href="https://heroku.com/deploy">
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy">
</a>

### Method 2: Deploy to Okteto

Another cloud-based deployment option.

[![Develop on Okteto](https://okteto.com/develop-okteto.svg)](https://cloud.okteto.com/deploy?repository=https://github.com/TeamUltroid/Ultroid)

### Method 3: Deploy Locally

For more control, you can deploy Ultroid on your own machine.

#### Easy Method (Recommended for Beginners)

-   **Linux:**
    ```bash
    wget -O locals.py https://git.io/JY9UM && python3 locals.py
    ```
-   **Windows:**
    ```powershell
    cd desktop ; wget https://git.io/JY9UM -o locals.py ; python locals.py
    ```
-   **Termux:**
    ```bash
    wget -O install-termux https://tiny.ultroid.tech/termux && bash install-termux
    ```

#### Traditional Method (For Advanced Users)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/TeamUltroid/Ultroid.git
    cd Ultroid
    ```
2.  **Create a virtual environment:**
    ```bash
    virtualenv -p /usr/bin/python3 venv
    . ./venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -U -r requirements.txt
    ```
4.  **Get your `SESSION` string:**
    -   **Linux:** `bash sessiongen`
    -   **Termux:** `bash sessiongen`
    -   **Windows:** `python -m pyUltroid.sessiongen`
5.  **Configure your bot:**
    -   Copy `.env.sample` to `.env`.
    -   Fill in the required variables in the `.env` file.
6.  **Run the bot:**
    -   **Linux/Termux:** `bash startup`
    -   **Windows:** `python -m pyUltroid`

---

## 📚 Documentation & Tutorials

-   **Official Documentation:** [ultroid.tech](http://ultroid.tech/)
-   **Full Video Tutorial:** [Watch on YouTube](https://www.youtube.com/watch?v=0wAV7pUzhDQ)
-   **Redis Tutorial:** [Read here](./resources/extras/redistut.md)

---

## 🔑 Necessary Variables

To run Ultroid, you'll need the following variables:

-   `SESSION`: Your Telegram account's session string. Get it from one of the methods below.

You'll also need one of the following databases:

-   **Redis:**
    -   `REDIS_URI`: Your Redis endpoint URL.
    -   `REDIS_PASSWORD`: Your Redis password.
-   **MongoDB:**
    -   `MONGO_URI`: Your MongoDB connection string.
-   **SQLDB:**
    -   `DATABASE_URL`: Your SQL database connection string.

---

## 🔒 Getting Your Session String

You can get your `SESSION` string in several ways:

-   **Repl.it:** [![Run on Repl.it](https://replit.com/badge/github/TeamUltroid/Ultroid)](https://replit.com/@TeamUltroid/UltroidStringSession)
-   **Telegram Bot:** [@SessionGeneratorBot](https://t.me/SessionGeneratorBot)
-   **Command Line:**
    -   **Linux:** `wget -O session.py https://git.io/JY9JI && python3 session.py`
    -   **Windows:** `cd desktop ; wget https://git.io/JY9JI -o ultroid.py ; python ultroid.py`
    -   **Termux:** `wget -O session.py https://git.io/JY9JI && python session.py`

---

## 💖 Contributors

A huge thanks to our amazing community for all their contributions!

<a href="https://github.com/TeamUltroid/Ultroid/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=TeamUltroid/Ultroid" />
</a>

---

## 📜 License

Ultroid is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html).

---

## 🙏 Credits

-   **TeamUltroid Devs:** For their continuous hard work.
-   **Lonami:** For the amazing [Telethon](https://github.com/LonamiWebs/Telethon) library.
-   **MarshalX:** For the powerful [PyTgCalls](https://github.com/MarshalX/tgcalls) library.

> Made with 💕 by [@TeamUltroid](https://t.me/TeamUltroid).
