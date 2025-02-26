def merge_and_count(arr, temp_arr, left, mid, right):
    i = left    # Left subarray index
    j = mid + 1 # Right subarray index
    k = left    # Merged array index
    inv_count = 0

    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp_arr[k] = arr[i]
            i += 1
        else:
            temp_arr[k] = arr[j]
            inv_count += (mid - i + 1)  # Count inversions
            j += 1
        k += 1

    while i <= mid:
        temp_arr[k] = arr[i]
        i += 1
        k += 1

    while j <= right:
        temp_arr[k] = arr[j]
        j += 1
        k += 1

    for i in range(left, right + 1):
        arr[i] = temp_arr[i]

    return inv_count

def count_inversions(arr, left, right, temp_arr):
    if left >= right:
        return 0

    mid = (left + right) // 2
    inv_count = count_inversions(arr, left, mid, temp_arr)
    inv_count += count_inversions(arr, mid + 1, right, temp_arr)
    inv_count += merge_and_count(arr, temp_arr, left, mid, right)

    return inv_count

def inversion_count(arr):
    temp_arr = arr.copy()
    return count_inversions(arr, 0, len(arr) - 1, temp_arr)

# Example Usage:
arr = [3,2,1]
print("Number of inversions:", inversion_count(arr))