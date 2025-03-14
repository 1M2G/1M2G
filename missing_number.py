#importing the numpy library
import numpy as np
def find_missing(lst):
    # Converting the list to numpy array
    arr = np.array(lst)
    # Creating a range of values between the minimum and maximum value in the list
    full_range = np.arange(lst[0], lst[-1]+1)
    # Calculating the missing values using numpy's setdiff1d() function
    missing = np.setdiff1d(full_range, arr)
    # Converting the numpy array back to a list and returning it
    return missing.tolist()
#Example usage
lst = [1, 2, 4, 6, 7, 9, 10]
missing = find_missing(lst)
print("The original list: ", lst)
print("The missing elements: ", missing)
