"""
Core tools for training models
"""
import os
from datetime import datetime

import deepdish as dd
import keras.callbacks as cb
from keras.layers import Input
from keras.metrics import mse
from keras.models import load_model
from keras.optimizers import Adam

from deepretina.metrics import kcc as cc

__all__ = ['train']


def load(filepath):
    """Reload a keras model"""
    return load_model(filepath, custom_objects={'cc': cc})


def train(model, data, lr=1e-2, bz=5000, nb_epochs=500, val_split=0.05):
    """Trains a model"""

    # build the model
    n_cells = data.y.shape[1]
    x = Input(shape=data.X.shape[1:], name='stimulus')
    mdl = model(x, n_cells)

    # compile the model
    mdl.compile(loss='poisson', optimizer=Adam(lr), metrics=[cc, mse])

    # store results in this directory
    name = mdl.name + datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
    base = f'../results/{name}'
    os.mkdir(base)

    # define model callbacks
    cbs = [cb.ModelCheckpoint(os.path.join(base, 'weights.{epoch:02d}-{val_loss:.2f}.h5')),
           cb.TensorBoard(log_dir=base, histogram_freq=1, batch_size=5000, write_grads=True),
           cb.ReduceLROnPlateau(min_lr=0, factor=0.2, patience=10),
           cb.CSVLogger(os.path.join(base, 'training.csv')),
           cb.EarlyStopping(monitor='val_loss', patience=10)]

    # train
    history = mdl.fit(x=data.X, y=data.y, batch_size=bz, epochs=nb_epochs,
                      callbacks=cbs, validation_split=val_split, shuffle=True)
    dd.io.save(os.path.join(base, 'history.h5'), history.history)
    return history
