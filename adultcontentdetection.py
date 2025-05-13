from selenium import webdriver
from selenium.webdriver.common.by import By
from transformers import pipeline, AutoImageProcessor, AutoModelForImageClassification
import torch
import requests
from PIL import Image
from io import BytesIO
import time
import json
from datetime import datetime

# ---------- SELENIUM ----------
def init_driver():
    try:
        driver = webdriver.Chrome()
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        exit(1)

def extract_text(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def extract_images(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        images = driver.find_elements(By.TAG_NAME, "img")
        return [img.get_attribute("src") for img in images]
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []

# ---------- TEXT ANALYSIS ----------
def analyze_text_with_transformers(text):
    try:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        labels = ["safe", "explicit", "porn", "adult", "NSFW"]
        return classifier(text[:512], candidate_labels=labels)
    except Exception as e:
        print(f"Error analyzing text: {e}")
        return None

# ---------- IMAGE ANALYSIS ----------
def load_nsfw_model():
    processor = AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
    model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
    return processor, model

def analyze_image_with_nsfw_local(image_url, processor, model):
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            return None
        image = Image.open(BytesIO(response.content)).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        labels = model.config.id2label
        return {labels[i]: float(probs[i]) for i in range(len(labels))}
    except Exception as e:
        print(f"Error analyzing image {image_url}: {e}")
        return None

# ---------- DECISION LOGIC ----------
def is_adult_content(text_result, image_results):
    try:
        text_adult = any(
            label.lower() in ["porn", "explicit", "adult", "nsfw"] and score > 0.6
            for label, score in zip(text_result["labels"], text_result["scores"])
        )
        image_adult = any(
            res and (res.get("porn", 0) + res.get("sexy", 0) + res.get("nsfw", 0)) > 0.5 for res in image_results
        )
        return text_adult or image_adult
    except Exception as e:
        print(f"Error determining adult content: {e}")
        return False

# ---------- SAVE RESULT ----------
def save_result(url, text_result, image_results, final_verdict):
    data = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "text_analysis": text_result,
        "image_analysis": image_results,
        "verdict": "NSFW Detected" if final_verdict else "Safe",
        "adult": "yes" if final_verdict else "no"
    }
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("\n✅ Result saved to result.json")

# ---------- MAIN ----------
def main(url):
    driver = init_driver()
    processor, model = load_nsfw_model()
    try:
        print("Extracting and analyzing text...")
        text = extract_text(driver, url)
        text_result = analyze_text_with_transformers(text)
        print("Text Analysis:", text_result)

        print("Extracting and analyzing images...")
        image_urls = extract_images(driver, url)
        image_results = []
        for img_url in image_urls[:10]:
            if img_url and img_url.startswith("http"):
                result = analyze_image_with_nsfw_local(img_url, processor, model)
                if result:
                    print(f"Image: {img_url} → {result}")
                    image_results.append(result)

        final_result = is_adult_content(text_result, image_results)
        print(f"\nFinal Verdict: {'NSFW Detected' if final_result else 'Safe'}")

        save_result(url, text_result, image_results, final_result)

    finally:
        driver.quit()

if __name__ == "__main__":
    main("https://www.instagram.com/")  # Change this to test other websites
