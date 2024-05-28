import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from PIL import Image
from tqdm import tqdm
import json
from flask import Flask, jsonify


def prepare_image(filepath):
    img = Image.open(filepath).resize((128, 128))
    img = np.array(img)
    img = img / 255.0  # Normalize the image
    return img

# Adding authentic images
X = []
Y = []

path = 'C:\\Users\\ceren\\OneDrive\\Desktop\\bitirme\\flask - Kopya\\static\\uploads\\CASIA2 Dataset\\Tp'
for filename in tqdm(os.listdir(path), desc="Processing Authentic Images"):
    if filename.endswith('jpg') or filename.endswith('png'):
        full_path = os.path.join(path, filename)
        X.append(prepare_image(full_path))
        Y.append(1)  # label for authentic images

print(f'Total authentic images: {len(X)}\nTotal labels: {len(Y)}')

# Adding forged images
path = 'C:\\Users\\ceren\\OneDrive\\Desktop\\bitirme\\flask - Kopya\\static\\uploads\\CASIA2 Dataset\\Au'
for filename in tqdm(os.listdir(path), desc="Processing Forged Images"):
    if filename.endswith('jpg') or filename.endswith('png'):
        full_path = os.path.join(path, filename)
        X.append(prepare_image(full_path))
        Y.append(0)  # label for forged images

print(f'Total images: {len(X)}\nTotal labels: {len(Y)}')

X = np.array(X)
Y = np.array(Y)
X = X.reshape(-1, 128, 128, 3)

# Split the dataset into training, validation, and testing sets
X_temp, X_test, Y_temp, Y_test = train_test_split(X, Y, test_size=0.05, random_state=5)
X_train, X_val, Y_train, Y_val = train_test_split(X_temp, Y_temp, test_size=0.2, random_state=5)

print(f'Training images: {len(X_train)} , Training labels: {len(Y_train)}')
print(f'Validation images: {len(X_val)} , Validation labels: {len(Y_val)}')
print(f'Test images: {len(X_test)} , Test labels: {len(Y_test)}')

# Build the CNN model
def build_model():
    model = Sequential()
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu', input_shape=(128, 128, 3)))
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu'))
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu'))
    model.add(Conv2D(64, (5, 5), padding='valid', activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(32, (5, 5), padding='valid', activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(GlobalAveragePooling2D())
    model.add(Dense(1, activation='sigmoid'))
    return model

model = build_model()
model.summary()

# Train the model
epochs = 10
batch_size = 32
init_lr = 1e-4
optimizer = Adam(learning_rate=init_lr)

model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])

early_stopping = EarlyStopping(monitor='val_accuracy', patience=10, verbose=1, mode='auto')

hist = model.fit(X_train, Y_train, batch_size=batch_size, epochs=epochs, validation_data=(X_val, Y_val), callbacks=[early_stopping])

# Save the model
model.save('my_model.h5')

# Save training history
history_dict = hist.history
file_path = 'training_history.json'
with open(file_path, 'w') as f:
    json.dump(history_dict, f)

print("Model and training history saved.")
