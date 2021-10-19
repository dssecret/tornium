# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

from math import exp, log
from random import randint, random


class Optimizer:
    def __init__(self, mode, cost, x0, cooling_mode='linear', t0=100, tf=0, max_steps=1000, bounds=[], damping=1, alpha=None):  # Based upon https://github.com/nathanrooy/simulated-annealing/blob/master/simulated_annealing/sa.py
        if mode in ('combinatorial', 'continuous'):
            raise Exception('The mode must either be "combinatorial" or "continuous".')
        elif cooling_mode in ('linear', 'exponential', 'logarithmic', 'quadratic'):
            raise Exception('The cooling mode must either be "linear", "exponential", "logarithmic", or "quadratic".')

        self.t = t0
        self.t0 = t0
        self.tf = tf
        self.max_steps = max_steps
        self.history = []
        self.mode = mode
        self.cooling_mode = cooling_mode
        self.cost_func = cost
        self.x0 = x0
        self.bounds = bounds
        self.damping = damping
        self.current_state = self.x0
        self.current_energy = cost(self.x0)
        self.best_state = self.current_state
        self.best_energy = self.current_energy

        if self.mode == 'combinatorial':
            self.get_neighbor = self.move_combinatorial
        else:
            self.get_neighbor = self.move_continuous

        if self.cooling_mode == 'linear':
            if alpha is not None:
                self.update = self.cooling_linear_multiplicative
                self.alpha = alpha
            else:
                self.update = self.cooling_linear_addative
        elif self.cooling_mode == 'quadratic':
            if alpha is not None:
                self.update = self.cooling_quadratic_multiplicative
                self.alpha = alpha
            else:
                self.update = self.cooling_quadratic_addative
        elif self.cooling_mode == 'logarithmic':
            if alpha is not None:
                self.alpha = alpha
            else:
                self.alpha = 0.8
            self.update = self.cooling_logarithmic
        else:
            if alpha is not None:
                self.alpha = alpha
            else:
                self.alpha = 0.8
            self.update = self.cooling_exponential

        self.step = 1
        self.accept = 0

        while self.step < self.max_steps and self.t >= self.tf and self.t > 0:
            proposed_neighbor = self.get_neighbor()
            neighbor_energy = self.cost_func(proposed_neighbor)
            energy_difference = neighbor_energy - self.current_energy

            if random() < self.safe_exp(-energy_difference / self.t):
                self.current_energy = neighbor_energy
                self.current_state = proposed_neighbor[:]
                self.accept += 1

            if neighbor_energy < self.best_energy:
                self.best_energy = neighbor_energy
                self.best_state = proposed_neighbor[:]

            self.history.append([
                self.step,
                self.t,
                self.current_energy,
                self.best_energy
            ])

            self.t = self.update(self.step)
            self.step += 1

        self.acceptance_rate = self.accept / self.step

    def move_combinatorial(self):
        p0 = randint(0, len(self.current_state) - 1)
        p1 = randint(0, len(self.current_state) - 1)

        neighbor = self.current_state[:]
        neighbor[p0], neighbor[p1] = neighbor[p1], neighbor[p0]

        return neighbor

    def move_continuous(self):
        neighbor = [item + ((random() - 0.5) * self.damping) for item in self.current_state]

        if self.bounds:
            for i in range(len(neighbor)):
                x_min, x_max = self.bounds[i]
                neighbor[i] = min(max(neighbor[i], x_min), x_max)

        return neighbor

    def cooling_linear_multiplicative(self, step):
        return self.t0 / (1 + self.alpha * step)

    def cooling_linear_addative(self, step):
        return self.tf + (self.t0 - self.tf) * ((self.max_steps - step)/self.max_steps)

    def cooling_quadratic_multiplicative(self, step):
        return self.tf / (1 + self.alpha * (step ** 2))

    def cooling_quadratic_addative(self, step):
        return self.tf + (self.t0 - self.tf) * ((self.max_steps - step) / self.max_steps) ** 2

    def cooling_exponential(self, step):
        return self.t0 * (self.alpha ** step)

    def cooling_logarithmic(self, step):
        return self.tf / (self.alpha * log(step + 1))

    def safe_exp(self, x):
        try:
            return exp(x)
        except:
            return 0
