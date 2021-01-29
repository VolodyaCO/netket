# Copyright 2021 The NetKet Authors - All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import jax
import flax
import numpy as np

from jax import numpy as jnp
from flax import struct

from typing import Any

from ..metropolis import MetropolisRule


@struct.dataclass
class ExchangeRule_(MetropolisRule):
    clusters: Any

    def transition(rule, sampler, machine, parameters, state, key, σ):
        n_chains = σ.shape[0]
        hilb = sampler.hilbert

        # pick a random cluster
        cluster_id = jax.random.randint(
            key, shape=(n_chains,), minval=0, maxval=rule.clusters.shape[0]
        )

        def scalar_update_fun(σ, cluster):
            # sites to be exchanged,
            si = rule.clusters[cluster, 0]
            sj = rule.clusters[cluster, 1]

            σp = jax.ops.index_update(σ, si, σ[sj])
            return jax.ops.index_update(σp, sj, σ[si])

        return (
            jax.vmap(scalar_update_fun, in_axes=(0, 0), out_axes=0)(σ, cluster_id),
            None,
        )


def compute_clusters(graph, d_max):
    clusters = []
    distances = np.asarray(graph.distances())
    size = distances.shape[0]
    for i in range(size):
        for j in range(i + 1, size):
            if distances[i][j] <= d_max:
                clusters.append((i, j))

    res_clusters = np.empty((len(clusters), 2), dtype=np.int64)

    for i, cluster in enumerate(clusters):
        res_clusters[i] = np.asarray(cluster)

    return res_clusters


def ExchangeRule(*, clusters=None, graph=None, d_max=1):
    if clusters is None and graph is not None:
        clusters = compute_clusters(graph, d_max)
    elif not (clusters is not None and graph is None):
        raise ValueError(
            """You must either provide the list of exchange-clusters or a netket graph, from
                          which clusters will be computed using the maximum distance d_max. """
        )

    return ExchangeRule_(jnp.array(clusters))
