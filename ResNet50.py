from loaddataset import processImages
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras import models
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

#
# Comment the next 4 lines if you are not using a GPU
gpus = tf.config.experimental.list_physical_devices("GPU")
print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices("GPU")))
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

keras.backend.clear_session()
workingDirectory = os.path.dirname(os.path.realpath(__file__))
imgDimensions = 224

images, labels, verImg, verLabels = processImages(
    workingDirectory, imgDimensions
)  # Load from loaddatset.py

#
# image dimensions
# default resnet18 dimensions are 224x224x3 (https://bit.ly/2VaOcyz)
#

img_height = imgDimensions
img_width = imgDimensions
img_channels = 3


def resNet(x):
    def commonLayers(y):
        y = layers.BatchNormalization()(y)
        y = layers.LeakyReLU()(y)
        return y

    def groupedConvolution(y, nb_channels, _strides):
        return layers.Conv2D(
            nb_channels, kernel_size=(3, 3), strides=_strides, padding="same"
        )(y)

    def resBlock(
        y, nb_channels_in, nb_channels_out, _strides=(1, 1), _project_shortcut=False
    ):
        shortcut = y
        y = layers.Conv2D(
            nb_channels_in, kernel_size=(1, 1), strides=(1, 1), padding="same"
        )(y)
        y = commonLayers(y)
        y = groupedConvolution(y, nb_channels_in, _strides=_strides)
        y = commonLayers(y)
        y = layers.Conv2D(
            nb_channels_out, kernel_size=(1, 1), strides=(1, 1), padding="same"
        )(y)
        # batch normalization is employed after aggregating the transformations and before adding to the shortcut
        y = layers.BatchNormalization()(y)
        if _project_shortcut or _strides != (1, 1):
            shortcut = layers.Conv2D(
                nb_channels_out, kernel_size=(1, 1), strides=_strides, padding="same"
            )(shortcut)
            shortcut = layers.BatchNormalization()(shortcut)
        y = layers.add([shortcut, y])
        y = layers.LeakyReLU()(y)
        return y

    x = layers.Conv2D(64, kernel_size=(7, 7), strides=(2, 2), padding="same")(x)
    x = commonLayers(x)
    x = layers.MaxPool2D(pool_size=(3, 3), strides=(2, 2), padding="same")(x)
    for i in range(3):
        project_shortcut = True if i == 0 else False
        x = resBlock(x, 128, 256, _project_shortcut=project_shortcut)
    for i in range(4):
        strides = (2, 2) if i == 0 else (1, 1)
        x = resBlock(x, 256, 512, _strides=strides)
    for i in range(6):
        strides = (2, 2) if i == 0 else (1, 1)
        x = resBlock(x, 512, 1024, _strides=strides)
    for i in range(3):
        strides = (2, 2) if i == 0 else (1, 1)
        x = resBlock(x, 1024, 2048, _strides=strides)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(1, activation="sigmoid")(x)
    return x


image_tensor = layers.Input(shape=(img_height, img_width, img_channels))
network_output = residual_network(image_tensor)

model = models.Model(inputs=[image_tensor], outputs=[network_output])

model.compile(
    optimizer="SGD", loss=keras.losses.BinaryCrossentropy(), metrics=["accuracy"]
)
model.save("ResNet50Pretrained.h5")

model.fit(images, labels, epochs=3, validation_data=(verImg, verLabels), shuffle=True)
