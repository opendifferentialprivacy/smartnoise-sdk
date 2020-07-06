
from sklearn.ensemble import AdaBoostClassifier, BaggingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier

from diffprivlib.models import LogisticRegression as DPLR

from opendp.whitenoise.synthesizers.mwem import MWEMSynthesizer
from opendp.whitenoise.synthesizers.quail import QUAILSynthesizer

SEED = 42

KNOWN_DATASETS = ['car'] #['wine'] #['nursery'] #['mushroom']

SYNTHESIZERS = [
    ('mwem', MWEMSynthesizer)
]

SYNTH_SETTINGS = {
    'mwem': {
        'nursery': {
            'Q_count':1000,
            'iterations':30,
            'mult_weights_iterations':20,
            'split_factor':8,
            'max_bin_count':400
        },
        'car': {
            'Q_count':1000,
            'iterations':30,
            'mult_weights_iterations':20,
            'split_factor':7,
            'max_bin_count':400
        },
        'mushroom': {
            'Q_count':3000,
            'iterations':30,
            'mult_weights_iterations':20,
            'split_factor':4,
            'max_bin_count':400
        },
        'wine': {
            'Q_count':1000,
            'iterations':30,
            'mult_weights_iterations':20,
            'split_factor':2,
            'max_bin_count':200
        }
    }
}

KNOWN_MODELS = [AdaBoostClassifier, BaggingClassifier,
               LogisticRegression, MLPClassifier, DecisionTreeClassifier,
               GaussianNB, BernoulliNB, MultinomialNB, RandomForestClassifier, ExtraTreesClassifier]

MODEL_ARGS = {
    'AdaBoostClassifier': {
        'random_state': SEED,
        'n_estimators': 100
    },
    'BaggingClassifier': {
        'random_state': SEED
    },
    'LogisticRegression': {
        'random_state': SEED,
        'max_iter': 1000,
        'multi_class': 'auto',
        'solver': 'lbfgs'
    },
    'MLPClassifier': {
        'random_state': SEED,
        'max_iter': 500
    },
    'DecisionTreeClassifier': {
        'random_state': SEED,
        'class_weight': 'balanced'
    },
    'GaussianNB': {
    },
    'BernoulliNB': {
    },
    'MultinomialNB': {
    },
    'RandomForestClassifier': {
        'random_state': SEED,
        'class_weight': 'balanced',
        'n_estimators': 200
    },
    'ExtraTreesClassifier': {
        'random_state': SEED,
        'class_weight': 'balanced',
        'n_estimators': 200
    }
}