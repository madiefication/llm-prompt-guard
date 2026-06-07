"""
Build script: generate dataset + train model.
Run once before starting the server (Render build command).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=== Step 1: Generating dataset ===")
from data.generate_dataset import main as gen_data
gen_data()

print("\n=== Step 2: Training ML model ===")
from engine.ml_classifier import train_and_save
train_and_save()

print("\n=== Build complete. Ready to serve. ===")
