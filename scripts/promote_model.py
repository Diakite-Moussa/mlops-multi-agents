"""Désigne un modèle comme « modèle en production » (l'Agent Release le fera au sprint 5).

Usage : python -m scripts.promote_model s3://models/adult_logreg/v3/model.pkl
"""
import sys

from core import registry

if len(sys.argv) != 2:
    sys.exit("usage : python -m scripts.promote_model <model_uri>")
print(registry.set_production(sys.argv[1]))
