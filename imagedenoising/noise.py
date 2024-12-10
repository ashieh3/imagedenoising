import numpy as np
from PIL import Image
import os
import cv2

def noisy(noise_typ,image):
    if noise_typ == "gauss":
      row,col,ch= image.shape
      mean = 10
      std = 25
      gauss = np.random.normal(mean,std,(row,col,ch))
      gauss = gauss.reshape(row,col,ch)
      noisy = image + gauss
      return noisy
    elif noise_typ == "s&p":
      row, col, ch = image.shape
      s_vs_p = 0.5
      amount = 0.04
      out = np.copy(image)
      
      # Salt mode
      num_salt = np.ceil(amount * image.size * s_vs_p)
      coords = [np.random.randint(0, i, int(num_salt)) for i in image.shape]
      out[tuple(coords)] = 255
      
      # Pepper mode
      num_pepper = np.ceil(amount * image.size * (1. - s_vs_p))
      coords = [np.random.randint(0, i, int(num_pepper)) for i in image.shape]
      out[tuple(coords)] = 0 
      
      return out
    elif noise_typ == "poisson":
      vals = len(np.unique(image))
      vals = 2 ** np.ceil(np.log2(vals))
      noisy = np.random.poisson(image * vals) / float(vals)
      return noisy
    elif noise_typ =="speckle":
      row,col,ch = image.shape
      gauss = np.random.randn(row,col,ch)
      gauss = gauss.reshape(row,col,ch)        
      noisy = image + image * gauss
      return noisy

if "__main__" == __name__:
  img = cv2.imread("image_to_be_noised.png")
  cv2.imwrite("gauss.jpg", noisy("gauss", img))
  cv2.imwrite("poisson.jpg", noisy("poisson", img))
  cv2.imwrite("speckle.jpg", noisy("speckle", img))
  cv2.imwrite("s&p.jpg", noisy("s&p", img))