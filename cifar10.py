from __future__ import print_function

import os.path

import densenet
import numpy as np
import sklearn.metrics as metrics

from tensorflow.keras.datasets import cifar10
from tensorflow.keras import utils
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import backend as K

batch_size = 100
nb_classes = 10
nb_epoch = 200
learning_rate = 1e-3

img_rows, img_cols = 32, 32
img_channels = 3

img_dim = (img_rows, img_cols, img_channels)
depth = 40
nb_dense_block = 3
growth_rate = 12
nb_filter = -1
dropout_rate = 0.0 # 0.0 for data augmentation

model = densenet.DenseNet(img_dim, classes=nb_classes, depth=depth, nb_dense_block=nb_dense_block,
                          growth_rate=growth_rate, nb_filter=nb_filter, dropout_rate=dropout_rate, weights=None)
print("Model created")

model.summary()
optimizer = Adam(lr=learning_rate) # Using Adam instead of SGD to speed up training
model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=["accuracy"])
print("Finished compiling")
print("Building model...")

(trainX, trainY), (testX, testY) = cifar10.load_data()

trainX = trainX.astype('float32')
testX = testX.astype('float32')

trainX = densenet.preprocess_input(trainX)
testX = densenet.preprocess_input(testX)

Y_train = utils.to_categorical(trainY, nb_classes)
Y_test = utils.to_categorical(testY, nb_classes)

generator = ImageDataGenerator(rotation_range=15,
                               width_shift_range=5./32,
                               height_shift_range=5./32,
                               horizontal_flip=True)

generator.fit(trainX, seed=0)

# Load model
weights_file="weights/DenseNet-40-12-CIFAR10.h5"
if os.path.exists(weights_file):
    #model.load_weights(weights_file, by_name=True)
    print("Model loaded.")

out_dir="weights/"

lr_reducer      = ReduceLROnPlateau(monitor='val_acc', factor=np.sqrt(0.1),
                                    cooldown=0, patience=5, min_lr=1e-5)
model_checkpoint= ModelCheckpoint(weights_file, monitor="val_acc", save_best_only=True,
                                  save_weights_only=True, verbose=1)

callbacks=[model_checkpoint]

historytemp = model.fit_generator(generator.flow(trainX, Y_train, batch_size=batch_size),
                    steps_per_epoch=len(trainX) // batch_size, epochs=nb_epoch,
                    callbacks=callbacks,
                    validation_data=(testX, Y_test),
                    validation_steps=testX.shape[0] // batch_size, verbose=1)

np_loss_history = np.array(historytemp.history['loss'])
np_acc_history = np.array(historytemp.history['val_acc'])
prefix = 'Dense_data/'
np.savetxt(prefix+'loss.txt', np_loss_history, delimiter=',')
np.savetxt(prefix+'acc.txt', np_acc_history, delimiter=',')

yPreds = model.predict(testX)
yPred = np.argmax(yPreds, axis=1)
yTrue = testY

accuracy = metrics.accuracy_score(yTrue, yPred) * 100
error = 100 - accuracy
print("Accuracy : ", accuracy)
print("Error : ", error)

