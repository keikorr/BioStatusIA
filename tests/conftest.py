import numpy as np
import pytest
from sklearn.datasets import make_classification


@pytest.fixture(scope="session")
def dados_binarios():
    X, y = make_classification(n_samples=150, n_features=6, n_informative=4,
                               weights=[0.65, 0.35], random_state=0)
    return X, y
