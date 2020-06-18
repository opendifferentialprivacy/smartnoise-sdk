import subprocess
import os

import pytest
import string
import pandas as pd

from opendp.whitenoise.metadata import CollectionMetadata
from opendp.whitenoise.synthesizers.dpgan.pate_gan import PATEGANSynthesizer

git_root_dir = subprocess.check_output("git rev-parse --show-toplevel".split(" ")).decode("utf-8").strip()

meta_path = os.path.join(git_root_dir, os.path.join("service", "datasets", "PUMS.yaml"))
csv_path = os.path.join(git_root_dir, os.path.join("service", "datasets", "PUMS.csv"))

schema = CollectionMetadata.from_file(meta_path)
df = pd.read_csv(csv_path)

synth = PATEGANSynthesizer()

class TestDPGAN:
    def test_fit(self):
        synth.fit(df.to_numpy())
        assert synth.generator
    
    def test_sample(self):
        sample_size = len(df)
        synthetic = synth.sample(sample_size)
        assert synthetic.shape == df.shape
