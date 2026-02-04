

# AI Marketing Agent – Full Pipeline (Study Project)

This repository contains an experimental **AI-powered marketing agent** that generates **one Social Media post (caption + image)** based on a company’s website and public social content.

The project combines **web scraping, LLM-based strategic copywriting, and image generation** into a simple end-to-end workflow, exposed via a Gradio interface.

> ⚠️ This is a **study / prototype project**.
> It is **not optimized**, **not production-ready**, and intended for learning and experimentation.

---

## Repository Structure

```
.
├── MarketingAgent.py   # Main application (Gradio UI + pipeline)
├── scraper.py          # Website content extraction
├── README.md
├── .env                # API keys (not committed)
├── .gitignore
```

---

## What It Does

1. Collects public content from:

   * Company website
   * LinkedIn page
   * Instagram profile
2. Uses a Large Language Model to:

   * Infer brand tone, audience, and positioning
   * Generate **exactly one** long-form Instagram caption
3. Generates:

   * **One single static Instagram image** (no carousel)

---

## Runtime Expectations

* Execution may take **up to ~2 minutes**
* This includes:

  * Selenium-based scraping
  * LLM inference
  * Image generation API calls

This behavior is expected and normal for this project.

---

## Requirements

### API Keys

You must provide your own API keys.

Create a `.env` file in the project root:

```env
HF_TOKEN=your_huggingface_token
OPENAI_API_KEY=your_openai_api_key
```

The application will not start without these keys.

---

## Python Dependencies

The following packages are used directly in the code and must be installed:

```bash
pip install \
  selenium \
  webdriver-manager \
  python-dotenv \
  huggingface-hub \
  openai \
  gradio
```

Additional standard-library modules are used (`os`, `json`, `uuid`, etc.) and do not require installation.

> Note: Google Chrome (or Chromium) must be installed for Selenium to work.

---

## Running Locally

```bash
python MarketingAgent.py
```

After Start, open the Gradio URL printed in the terminal.

---

## Known Limitations

* Fragile scraping (DOM changes may break Instagram or LinkedIn scraping)
* No caching or retry logic
* No performance or cost optimization
* Single-post generation only

---

## Disclaimer

This project is intended as a **learning and exploration exercise**, not a production system.
Significant refactoring would be required for real-world use.

