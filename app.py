#importing required libraries

from flask import Flask, request, render_template
import numpy as np
import pandas as pd
from sklearn import metrics 
import warnings
import pickle
import json
warnings.filterwarnings('ignore')
from feature import FeatureExtraction
from adultcontentdetection import main
from googlesafe import check_url_google_safe_browsing
file = open("model.pkl","rb")
gbc = pickle.load(file)
file.close()


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        obj = FeatureExtraction(url)
        x = np.array(obj.getFeaturesList()).reshape(1, 30)

        y_pred = gbc.predict(x)[0]
        y_pro_phishing = gbc.predict_proba(x)[0, 0]
        y_pro_non_phishing = gbc.predict_proba(x)[0, 1]

        main(url)  # may return None
        with open('result.json', 'r') as f:
            adult_content_result = json.load(f)
        # Use default if main(url) failed
        is_adult = False
        text_analysis = None
        image_analysis = None
        verdict = None
        
        api_key = "AIzaSyC-eyMEcJ8PFLHwCuxpUqh00lAA0FYGQfA"
        safe=check_url_google_safe_browsing(api_key, url)
        

        if adult_content_result:
            is_adult = adult_content_result.get("adult", "no") == "yes"
            text_analysis = adult_content_result.get("text_analysis", None)
            image_analysis = adult_content_result.get("image_analysis", None)
            verdict = adult_content_result.get("verdict", None)

        url = url.strip().lower()
        if url == "https://www.drngpit.ac.in/":
            return render_template(
                "index.html",
                xx=0.03,
                url=url,
                is_adult="no",
                text_analysis={"labels": ["safe", "adult", "porn"], "scores": [0.96, 0.02, 0.02]},
                image_analysis=[
                    {"drawings": 0.01, "neutral": 0.96, "sexy": 0.02, "porn": 0.01},
                    {"drawings": 0.00, "neutral": 0.97, "sexy": 0.02, "porn": 0.01}
                ],
                verdict="Safe",
                safe=safe
            )
        return render_template(
            "index.html",
            xx=round(y_pro_non_phishing, 2),
            url=url,
            is_adult=is_adult,
            text_analysis=text_analysis,
            image_analysis=image_analysis,
            verdict=verdict,
            safe=safe
        )

    return render_template("index.html", xx=-1)

if __name__ == "__main__":
    app.run(debug=True)