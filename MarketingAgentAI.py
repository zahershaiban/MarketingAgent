
"""
MARKETING AGENT (FREE STACK – FULL PIPELINE)
"""

# ======================================================
# IMPORTS
# ======================================================
import os
import base64
import uuid
import time
import json
import re
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from scraper import fetch_website_contents

# 🔁 TEXT → Hugging Face (LLaMA)
from huggingface_hub import InferenceClient

# 🖼️ IMAGES → OpenAI (unchanged)
from openai import OpenAI

import gradio as gr


# ======================================================
# LOAD ENVIRONMENT VARIABLES
# ======================================================
load_dotenv(override=True)

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("❌ HF_TOKEN missing in .env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY missing in .env")

hf_client = InferenceClient(token=HF_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ Hugging Face (LLaMA) configured")
print("✅ OpenAI (Images) configured")


# ======================================================
# SELENIUM DRIVER
# ======================================================
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ======================================================
# SCRAPE INSTAGRAM POSTS
# ======================================================
def scrape_instagram_posts(instagram_url, max_posts=2):
    driver = get_driver()
    driver.get(instagram_url)
    time.sleep(5)

    captions = []

    try:
        links = driver.find_elements(By.XPATH, "//article//a")[:max_posts]
        for link in links:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", link)
                time.sleep(3)

                caption = driver.find_element(
                    By.XPATH, "//div[@role='dialog']//span"
                ).text
                captions.append(caption)

                driver.execute_script(
                    "document.querySelector('div[role=\"dialog\"] button').click();"
                )
                time.sleep(2)

            except Exception as e:
                print("⚠️ Skipping Instagram post:", e)

    except Exception as e:
        print("⚠️ Instagram scrape failed:", e)

    driver.quit()
    return captions


# ======================================================
# SCRAPE LINKEDIN POSTS
# ======================================================
def scrape_linkedin_posts(linkedin_url, max_posts=2):
    driver = get_driver()
    driver.get(linkedin_url)
    time.sleep(5)

    posts = []
    try:
        elements = driver.find_elements(
            By.XPATH, "//div[contains(@class,'feed-shared-update-v2')]"
        )[:max_posts]
        for el in elements:
            posts.append(el.text)
    except Exception as e:
        print("⚠️ LinkedIn scrape failed:", e)

    driver.quit()
    return posts


# ======================================================
# COLLECT SOCIAL CONTEXT
# ======================================================
def collect_brand_social_context(linkedin_url, instagram_url):
    return (
        "\n\n".join(scrape_linkedin_posts(linkedin_url)),
        "\n\n".join(scrape_instagram_posts(instagram_url)),
    )

# ======================================================
# PROMPTS (UNCHANGED — ONLY ADDITIONS)
# ======================================================
SYSTEM_PROMPT = """You are a senior growth marketing strategist and creative director with
10+ years of experience working with B2B technology companies, SaaS products,
and professional service firms.

You think in terms of:
- Brand positioning and differentiation
- Audience psychology and decision-making
- Platform-specific performance (Instagram-first)
- Clear messaging hierarchy (hook → value → proof → action)

You avoid generic marketing language, buzzwords, and vague claims.
You prefer clarity, specificity, and confident positioning.

You generate content that could realistically be approved by a professional
marketing team and published without edits.

You strictly follow formatting instructions and output requirements.
"""

USER_PROMPT_PREFIX = """You are given information about a company from multiple sources.

Your objective is to behave like a professional marketing team and produce
Instagram content that is:
- On-brand
- Strategically sound
- Visually coherent
- Optimized for attention and clarity

Create EXACTLY ONE Instagram post.

━━━━━━━━━━━━━━━━━━━━━━
CRITICAL VISUAL CONSTRAINT
━━━━━━━━━━━━━━━━━━━━━━
The image must be:
- ONE single static image
- NOT a carousel
- NOT a multi-slide concept
- NOT a sequence of frames or pages

If the idea involves multiple points, steps, or categories, you must
SUMMARIZE them into ONE cohesive overview visual.

Think in terms of:
- A single capability map
- A structured overview
- A clean architecture-style visual
- A dense but readable one-frame composition

Do NOT describe slides, pages, or numbered frames.
Do NOT use language like “Slide 1”, “Slide 2”, or “Carousel”.

━━━━━━━━━━━━━━━━━━━━━━
CAPTION STYLE ADD-ON
━━━━━━━━━━━━━━━━━━━━━━
The caption should resemble a long-form LinkedIn thought-leadership post:
- Strategic
- Insight-driven
- Short paragraphs
- Optional bullet points
- Consultant / CIO-level tone
━━━━━━━━━━━━━━━━━━━━━━
CAPTION DEPTH REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━
The caption MUST be long-form and editorial in style.

Structure the caption as follows:
1. A strong, scroll-stopping headline (can include a colon)
2. 1–2 short paragraphs explaining the core problem or tension
3. A bullet list (3–5 bullets) with concrete points, themes, or takeaways
4. A final strong concluding statement that reinforces urgency or value

The caption must:
- Be at least 120–180 words
- Read like a thought-leadership post, not ad copy
- Avoid generic marketing phrases like “unlock”, “empower”, “seamless”, “next level”
- Sound like it was written by a senior consultant or strategist

Line breaks are REQUIRED.
Bullet points are REQUIRED.
━━━━━━━━━━━━━━━━━━━━━━
BRAND COLOR & VISUAL CONSISTENCY
━━━━━━━━━━━━━━━━━━━━━━
You must respect the existing brand identity.

Infer the brand’s color palette from:
- The company website
- Instagram posts
- LinkedIn posts

Rules:
- Use ONLY colors that are clearly present or strongly implied
- Do NOT invent new colors
- Do NOT redesign or modernize the palette
- Preserve the brand’s visual DNA

In the "visual_direction" field:
- Explicitly reference the dominant brand colors (e.g. dark blue, white, muted gray)
- Describe contrast, hierarchy, and background using those colors
- Ensure the image would feel native if placed next to existing posts

If the brand uses a restrained or corporate palette, keep the visual restrained.
If the brand uses bold or high-contrast colors, reflect that appropriately.
━━━━━━━━━━━━━━━━━━━━━━
EMOJI USAGE (SUBTLE & PROFESSIONAL)
━━━━━━━━━━━━━━━━━━━━━━
Use emojis sparingly and intentionally.

Rules:
- Use a maximum of 3–6 emojis in the entire caption
- Emojis must support meaning or structure, not decoration
- Prefer simple, professional emojis (e.g. 📌 ⚙️ 📊 🚀 🔍 ⏱️)
- Emojis may be used:
  - In the headline (optional, max 1)
  - To introduce the bullet list
  - To subtly emphasize the concluding statement

Do NOT:
- Use emojis in every paragraph
- Use playful or childish emojis (e.g. 😂🔥💯😍)
- Overuse arrows or symbols

The tone must remain consultant-grade and CIO-appropriate.
━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (STRICT — VALID JSON ONLY)
━━━━━━━━━━━━━━━━━━━━━━

{
  "brand_analysis": {
    "tone": "",
    "target_audience": "",
    "value_proposition": "",
    "visual_style": "",
    "cta_style": ""
  },
  "post": {
    "angle": "",
    "caption": "",
    "hashtags": "",
    "call_to_action": "",
    "visual_direction": ""
  }
}

CONTENT STARTS BELOW
"""


def build_prompt(website, linkedin, instagram):
    return USER_PROMPT_PREFIX + f"""
WEBSITE:
{website}

LINKEDIN:
{linkedin}

INSTAGRAM:
{instagram}
"""


# ======================================================
# 🔧 LLaMA JSON EXTRACTOR (ADDED)
# ======================================================import json


def extract_json_llama(text: str) -> dict:
    if not text:
        raise ValueError("Empty model output")

    # Remove markdown fences
    text = re.sub(r"```[a-zA-Z]*", "", text)

    # Extract the first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")

    json_str = match.group(0)

    # Normalize typography only
    json_str = (
        json_str
        .replace("\r", "")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    # 🔑 Escape newlines ONLY inside strings
    def escape_newlines_in_strings(s: str) -> str:
        result = []
        in_string = False
        escape = False

        for ch in s:
            if ch == '"' and not escape:
                in_string = not in_string
            if ch == "\n" and in_string:
                result.append("\\n")
            else:
                result.append(ch)

            escape = (ch == "\\" and not escape)

        return "".join(result)

    json_str = escape_newlines_in_strings(json_str)

    # Remove trailing commas (LLaMA sometimes adds them)
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ RAW MODEL OUTPUT:")
        print(text)
        print("❌ FINAL JSON STRING:")
        print(json_str)
        raise e




# ======================================================
# GENERATE POSTS (TEXT – LLAMA)
# ======================================================
def generate_instagram_posts(website_url, linkedin_text, instagram_text):
    website = fetch_website_contents(website_url)
    user_prompt = build_prompt(website, linkedin_text, instagram_text)

    response = hf_client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
                           + "\n\nRETURN VALID JSON ONLY. NO EXPLANATIONS."
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1100,
    )

    raw = response.choices[0].message.content
    return extract_json_llama(raw)


# ======================================================
# GENERATE IMAGE (UNCHANGED)
# ======================================================
def generate_instagram_image(caption, visual_direction):
    prompt = f"""
Create a professional Instagram marketing image.

Caption context:
{caption}

Visual direction:
{visual_direction}

Rules:
- Square format
- High contrast
- Mobile-first
- No logos
"""

    result = openai_client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    os.makedirs("generated_images", exist_ok=True)
    image_path = f"generated_images/{uuid.uuid4().hex}.png"

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return image_path


# ======================================================
# STEP 1: GENERATE TEXT
# ======================================================
def run_text_only(website_url, linkedin_url, instagram_url):
    linkedin_text, instagram_text = collect_brand_social_context(
        linkedin_url, instagram_url
    )

    data = generate_instagram_posts(
        website_url, linkedin_text, instagram_text
    )

    post = data.get("post", {})

    return (
        data.get("brand_analysis", {}),
        post.get("caption", ""),
        post.get("visual_direction", ""),
        "✅ Caption ready. Edit if needed, then click Generate Image."
    )


# ======================================================
# STEP 2: GENERATE IMAGE
# ======================================================
def run_image_only(caption, visual):
    if not caption.strip() or not visual.strip():
        return "⚠️ Caption or visual direction missing.", []

    image = generate_instagram_image(caption, visual)
    return "✅ Image generated!", [image]


# ======================================================
# GRADIO UI (UNCHANGED)
# ======================================================
with gr.Blocks(title="AI Marketing Agent") as demo:
    gr.Markdown("# 📸 AI Marketing Agent")
    gr.Markdown("Generate one Instagram caption and one image")

    with gr.Row():
        website_input = gr.Textbox(label="Company Website URL")
        linkedin_input = gr.Textbox(label="LinkedIn Page")
        instagram_input = gr.Textbox(label="Instagram Profile")

    run_text_button = gr.Button("1️⃣ Generate Caption")

    brand_analysis_output = gr.JSON(label="Brand Analysis")
    caption_box = gr.Textbox(label="Caption")
    visual_box = gr.Textbox(label="Visual Direction")

    run_image_button = gr.Button("2️⃣ Generate Image")

    status = gr.Markdown()
    output_images = gr.Gallery(label="Generated Image", columns=1)

    run_text_button.click(
        fn=run_text_only,
        inputs=[website_input, linkedin_input, instagram_input],
        outputs=[brand_analysis_output, caption_box, visual_box, status],
    )

    run_image_button.click(
        fn=run_image_only,
        inputs=[caption_box, visual_box],
        outputs=[status, output_images],
    )


if __name__ == "__main__":
    demo.launch()
