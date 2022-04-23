import pandas as pd
import torch
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def sentiment(row):
    model_name = "uer/roberta-base-finetuned-dianping-chinese"     # 选择想要的模型
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    classifier = pipeline('sentiment-analysis',model=model,tokenizer=tokenizer)
    emotional_value = classifier(row)
    return emotional_value
