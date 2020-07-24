import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from torchdp import PrivacyEngine, utils, autograd_grad_sample
from opendp.whitenoise.synthesizers.pytorch.pate import pate, moments_acc, weights_init
import math

class DPGANGenerator(nn.Module):
    def __init__(self, latent_dim, output_dim, binary=True):
        super(DPGANGenerator, self).__init__()
        def block(in_, out, Activation):
            return nn.Sequential(
                nn.Linear(in_, out, bias=False),
                nn.LayerNorm(out),
                Activation(),
            )

        self.layer_0 = block(latent_dim, latent_dim, nn.Tanh if binary else lambda: nn.LeakyReLU(0.2))
        self.layer_1 = block(latent_dim, latent_dim, nn.Tanh if binary else lambda: nn.LeakyReLU(0.2))
        self.layer_2 = block(latent_dim, output_dim, nn.Tanh if binary else lambda: nn.LeakyReLU(0.2))

    def forward(self, noise):
        noise = self.layer_0(noise) + noise
        noise = self.layer_1(noise) + noise
        noise = self.layer_2(noise)
        return noise


class DPGANDiscriminator(nn.Module):
    def __init__(self, input_dim, wasserstein=False):
        super(DPGANDiscriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 2*input_dim // 3),
            nn.LeakyReLU(0.2),
            nn.Linear(2*input_dim // 3, input_dim // 3),
            nn.LeakyReLU(0.2),
            nn.Linear(input_dim // 3, 1)
        )

        if not wasserstein:
            self.model.add_module("activation", nn.Sigmoid())

    def forward(self, x):
        return self.model(x)

class DPGAN:
    def __init__(self, 
                 binary=False,
                 latent_dim=64, 
                 batch_size=64,
                 epochs=1000,
                 delta=1e-5,
                 epsilon=1.0):
        self.binary = binary
        self.latent_dim = latent_dim
        self.batch_size = batch_size
        self.epochs = epochs
        self.delta = delta
        self.epsilon = epsilon

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.pd_cols = None
        self.pd_index = None

    def train(self, data, epsilon=None):
        if epsilon:
            self.epsilon = epsilon

        if isinstance(data, pd.DataFrame):
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='ignore')
            self.pd_cols = data.columns
            self.pd_index = data.pd_index
            data = data.to_numpy()
        elif not isinstance(data, np.ndarray):
            raise ValueError("Data must be a numpy array or pandas dataframe")

        dataset = TensorDataset(torch.from_numpy(data.astype('float32')).to(self.device))
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=True)

        self.generator = DPGANGenerator(self.latent_dim, data.shape[1], binary=self.binary).to(self.device)
        discriminator = DPGANDiscriminator(data.shape[1]).to(self.device)
        optimizer_d = optim.Adam(discriminator.parameters(), lr=4e-4)

        privacy_engine = PrivacyEngine(
            discriminator,
            batch_size=self.batch_size,
            sample_size=len(data),
            alphas=[1 + x / 10.0 for x in range(1, 100)] + list(range(12, 64)),
            noise_multiplier=3.5,
            max_grad_norm=1.0,
            clip_per_layer=True
        )

        privacy_engine.attach(optimizer_d)
        optimizer_g = optim.Adam(self.generator.parameters(), lr=1e-4)

        criterion = nn.BCELoss()

        for epoch in range(self.epochs):
            for i, data in enumerate(dataloader):
                discriminator.zero_grad()

                real_data = data[0].to(self.device)

                # train with fake data
                noise = torch.randn(self.batch_size, self.latent_dim, 1, 1, device=self.device)
                noise = noise.view(-1, self.latent_dim)
                fake_data = self.generator(noise)
                label_fake = torch.full((self.batch_size,), 0, device=self.device)
                output = discriminator(fake_data.detach())
                loss_d_fake = criterion(output, label_fake)
                loss_d_fake.backward()
                optimizer_d.step()

                # train with real data
                label_true = torch.full((self.batch_size,), 1, device=self.device)
                output = discriminator(real_data.float())
                loss_d_real = criterion(output, label_true)
                loss_d_real.backward()
                optimizer_d.step()

                loss_d = loss_d_real + loss_d_fake

                max_grad_norm = []
                for p in discriminator.parameters():
                    param_norm = p.grad.data.norm(2).item()
                    max_grad_norm.append(param_norm)

                privacy_engine.max_grad_norm = max_grad_norm

                # train generator
                self.generator.zero_grad()
                label_g = torch.full((self.batch_size,), 1, device=self.device)
                output_g = discriminator(fake_data)
                loss_g = criterion(output_g, label_g)
                loss_g.backward()
                optimizer_g.step()

                # manually clear gradients
                for p in discriminator.parameters():
                   if hasattr(p, "grad_sample"):
                       del p.grad_sample
                # autograd_grad_sample.clear_backprops(discriminator)

                if self.delta is None:
                    self.delta = 1 / data.shape[0]

                epsilon, best_alpha = optimizer_d.privacy_engine.get_privacy_spent(self.delta)

            if self.epsilon < epsilon:
                break

    def generate(self, n):
        steps = n // self.batch_size + 1
        data = []
        for i in range(steps):
            noise = torch.randn(self.batch_size, self.latent_dim, 1, 1, device=self.device)
            noise = noise.view(-1, self.latent_dim)

            fake_data = self.generator(noise)
            data.append(fake_data.detach().cpu().numpy())

        data = np.concatenate(data, axis=0)
        data = data[:n]

        return data 

class PATEGenerator(nn.Module):
    def __init__(self, latent_dim, hidden_dims, output_dim):
        super(PATEGenerator, self).__init__()
        previous_layer_dim = latent_dim

        model = []
        for i, layer_dim in enumerate(list(hidden_dims)):
            model.append(nn.Linear(previous_layer_dim, layer_dim))
            model.append(nn.BatchNorm1d(layer_dim))
            model.append(nn.ReLU())
            previous_layer_dim = layer_dim
        model.append(nn.Linear(previous_layer_dim, output_dim))

        self.model = nn.Sequential(*model)

    def forward(self, noise):
        data = self.model(noise)
        return data

class PATEDiscriminator(nn.Module):
    def __init__(self, input_dim, hidden_dims):
        super(PATEDiscriminator, self).__init__()
        previous_layer_dim = input_dim

        model = []
        if isinstance(hidden_dims, tuple):
            for i, layer_dim in enumerate(list(hidden_dims)):
                model.append(nn.Linear(previous_layer_dim, layer_dim))
                model.append(nn.LeakyReLU(0.2))
                model.append(nn.Dropout(0.5))
                previous_layer_dim = layer_dim
        else:
            model.append(nn.Linear(previous_layer_dim, hidden_dims))
            previous_layer_dim = hidden_dims
        model.append(nn.Linear(previous_layer_dim, 1))
        model.append(nn.Sigmoid())

        self.model = nn.Sequential(*model)

    def forward(self, input):
        output = self.model(input)
        return output.view(-1)

class PATEGAN:
    def __init__(self,
                 binary=False,
                 latent_dim=64,
                 gen_dim=(128, 64, 128),
                 batch_size=64,
                 teacher_iters=5,
                 student_iters=5,
                 budget=1.0,
                 delta=1e-5):
        self.binary = binary
        self.latent_dim = latent_dim
        self.gen_dim = gen_dim
        self.batch_size = batch_size
        self.teacher_iters = teacher_iters
        self.student_iters = student_iters
        self.budget = budget
        self.delta = delta
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.pd_cols = None
        self.pd_index = None

    def train(self, data, epsilon=None):
        if epsilon:
            self.epsilon = epsilon

        if isinstance(data, pd.DataFrame):
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='ignore')
            self.pd_cols = data.columns
            self.pd_index = data.pd_index
            data = data.to_numpy()
        elif not isinstance(data, np.ndarray):
            raise ValueError("Data must be a numpy array or pandas dataframe")

        data_dim = data.shape[1]
        self.num_teachers = int(len(data) / 1000)
        if self.num_teachers < 1:
            self.num_teachers = 1

        data_partitions = np.array_split(data, self.num_teachers)
        tensor_partitions = [TensorDataset(torch.from_numpy(data.astype('double')).to(self.device)) for data in data_partitions]

        loader = []
        for teacher_id in range(self.num_teachers):
            loader.append(DataLoader(tensor_partitions[teacher_id], batch_size=self.batch_size, shuffle=True))

        self.generator = PATEGenerator(self.latent_dim, self.gen_dim, data_dim).double().to(self.device)
        self.generator.apply(weights_init)

        student_dim = (data_dim, int(data_dim/2), data_dim)
        student_disc = PATEDiscriminator(data_dim, student_dim).double().to(self.device)
        student_disc.apply(weights_init)

        teacher_disc = [PATEDiscriminator(data_dim, data_dim).double().to(self.device) for i in range(self.num_teachers)]
        for i in range(self.num_teachers):
            teacher_disc[i].apply(weights_init)

        optimizer_g = optim.Adam(self.generator.parameters(), lr=1e-4)
        optimizer_s = optim.Adam(student_disc.parameters(), lr=1e-4)
        optimizer_t = [optim.Adam(teacher_disc[i].parameters(), lr=1e-4) for i in range(self.num_teachers)]

        criterion = nn.BCELoss()

        noise_multiplier = 1e-3
        alphas = torch.tensor([0.0 for i in range(100)])
        l_list = 1 + torch.tensor(range(100))
        epsilon = 0

        while epsilon < self.budget:

            # train teacher discriminators
            for t_2 in range(self.teacher_iters):
                for i in range(self.num_teachers):
                    real_data, category = None, None
                    for j, data in enumerate(loader[i], 0):
                        real_data = data[0].to(self.device)
                        break

                    optimizer_t[i].zero_grad()

                    # train with real data
                    label_real = torch.full((real_data.shape[0],), 1, device=self.device)
                    output = teacher_disc[i](real_data)
                    loss_t_real = criterion(output, label_real.double())
                    loss_t_real.backward()

                    # train with fake data
                    noise = torch.rand(self.batch_size, self.latent_dim, device=self.device)
                    label_fake = torch.full((self.batch_size,), 0, device=self.device)
                    fake_data = self.generator(noise.double())
                    output = teacher_disc[i](fake_data)
                    loss_t_fake = criterion(output, label_fake.double())
                    loss_t_fake.backward()
                    optimizer_t[i].step()

            # train student discriminator
            for t_3 in range(self.student_iters):
                noise = torch.rand(self.batch_size, self.latent_dim, device=self.device)
                fake_data = self.generator(noise.double())
                predictions, votes = pate(fake_data, teacher_disc, noise_multiplier)
                output = student_disc(fake_data.detach())

                # update moments accountant
                alphas = alphas + moments_acc(self.num_teachers, votes, noise_multiplier, l_list)

                loss_s = criterion(output, predictions.to(self.device))
                loss_s.backward()
                optimizer_s.step()

            # train generator
            label_g = torch.full((self.batch_size,), 1, device=self.device)
            noise = torch.rand(self.batch_size, self.latent_dim, device=self.device)
            gen_data = self.generator(noise.double())
            output_g = student_disc(gen_data)
            loss_g = criterion(output_g, label_g.double())
            loss_g.backward()
            optimizer_g.step()

            epsilon = min((alphas - math.log(self.delta)) / l_list)

    def generate(self, n):
        steps = n // self.batch_size + 1
        data = []
        for i in range(steps):
            noise = torch.randn(self.batch_size, self.latent_dim, device=self.device)
            noise = noise.view(-1, self.latent_dim)

            fake_data = self.generator(noise.double())
            data.append(fake_data.detach().cpu().numpy())

        data = np.concatenate(data, axis=0)
        data = data[:n]

        return data 