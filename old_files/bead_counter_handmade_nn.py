__author__ = 'raphey'

import numpy as np
import cv2
from hidden_layer_bead_classifier import fwd_pass


def distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5


def bead_filter(img, x_c, y_c, window=0, threshold=0.6):
    """
    Uses a linear classifier to determine of a 28x28 image centered at x_c, y_c is a bead.
    Slides a window around to look for maximum likelihood; also stores the maximum center in a
    global list after checking that it isn't too close to an already-found center.
    """
    if not (14 + window <= x_c <= len(img[0]) - 14 - window and 14 + window <= y_c <= len(img) - 14 - window):
        return False

    max_likelihood = 0.0
    best_x, best_y = 0, 0       # Not using this now, but later want to know where best_x and _best_y are

    for x_shift in range(-window, window + 1):
        for y_shift in range(-window, window + 1):
            x_min = x_c - 14 + x_shift
            y_min = y_c - 14 + y_shift
            bead_img = img[y_min: y_min + 28, x_min: x_min + 28].astype(float)
            min_val = bead_img.min()
            max_val = bead_img.max()
            scaled_img = (bead_img - min_val) / (max_val - min_val)

            # Alternate way to scale image that doesn't seem to work as well (requires corresponding training.
            # scaled_img = bead_img / 256.0

            reshaped_img = scaled_img.reshape(1, 784)

            _, bead_likelihood = fwd_pass(reshaped_img, weight1, bias1, weight2, bias2)

            if bead_likelihood > max_likelihood:
                max_likelihood = bead_likelihood
                best_x, best_y = x_c + x_shift, y_c + y_shift

    if max_likelihood > threshold:
        if all(distance(best_x, best_y, x, y) > 8.0 for x, y in filtered_beads):
            filtered_beads.append((best_x, best_y))
            return True
    else:
        return False


def save_bead(img, x_c, y_c, a=14):
    """
    Write the given portion of image to a new .png file with dimensions 2a by 2a.
    """
    if not (a <= x_c <= len(img[0]) - a and a <= y_c <= len(img) - a):
        return
    bead_img = img[y_c - a: y_c + a, x_c - a: x_c + a]

    count_label = str(100000 + bead_counter)[1:]
    cv2.imwrite('training_data/sample_{}_{}_x{}_y{}.png'.format(2 * a, count_label, x_c, y_c), bead_img)


# Load image, make a copy for final output, and convert image to grayscale
image_path = 'images/test_array_1_4x.png'
image = cv2.imread(image_path)
output = image.copy()
grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Perform circle detection for droplets and beads
droplets =cv2.HoughCircles(grayscale_image, cv2.HOUGH_GRADIENT, 1, 12, param1=80, param2=30, minRadius=65, maxRadius=93)
beads = cv2.HoughCircles(grayscale_image, cv2.HOUGH_GRADIENT, 1, 8, param1=40, param2=4, minRadius=10, maxRadius=12)

# Alternate bead detection allowing for tiny white circles in bead centers
# beads = cv2.HoughCircles(grayscale_image, cv2.HOUGH_GRADIENT, 1, 8, param1=40, param2=4, minRadius=3, maxRadius=12)


filtered_beads = []

# Load weights and biases for classifier
weight1 = np.load('classifier_data/hidden_layer_classifier/weight1.npy')
bias1 = np.load('classifier_data/hidden_layer_classifier/bias1.npy')
weight2 = np.load('classifier_data/hidden_layer_classifier/weight2.npy')
bias2 = np.load('classifier_data/hidden_layer_classifier/bias2.npy')

# convert the (x, y) coordinates and radius of the droplets and beads to integers
droplets = np.round(droplets[0, :]).astype('int')
valid_droplets = []
beads = np.round(beads[0, :]).astype('int')
droplet_clusters = []
cluster_lookup = {}

# This will group together together the droplet circles, since each droplet is made of multiple circles.
for x, y, r in droplets:
    if not (120 < x < 1672 and 120 < y < 1672):       # Check that droplets are inbounds
        continue

    valid_droplets.append((x, y, r))

    for i, dc in enumerate(droplet_clusters):
        if any(distance(x, y, x2, y2) < 40 for x2, y2, _ in dc):        # Are any droplet circles more than 40 away?
            cluster_lookup[(x, y, r)] = i
            droplet_clusters[i].append((x, y, r))
            break
    else:
        cluster_lookup[(x, y, r)] = len(droplet_clusters)
        droplet_clusters.append([(x, y, r)])

cluster_count = [0] * len(droplet_clusters)
cluster_beads = [[] for _ in range(len(droplet_clusters))]


bead_counter = 0

# For each bead, we want to check if it is valid, and if so, link it to its containing droplet cluster
for x, y, r in beads:
    if not bead_filter(grayscale_image, x, y, window=4):
        continue

    bead_counter += 1   # Not currently being used, but this is needed for saving

    closest_droplet_circle = tuple(min(droplets, key=lambda z: distance(x, y, z[0], z[1])))
    if closest_droplet_circle not in valid_droplets:
        continue
    i = cluster_lookup[closest_droplet_circle]
    if any(distance(x, y, d_x, d_y) < d_r for d_x, d_y, d_r in droplet_clusters[i]):
        # bead is enclosed by cluster i
        cluster_beads[i].append((x, y, r))

# Go through each droplet cluster and print the droplet boundaries (commented out), the beads, and the count
for i, dc in enumerate(droplet_clusters):
    color = (np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256))

    for x, y, r in cluster_beads[i]:
        cv2.circle(output, (x, y), r, color, 1)

    avg_x = int(sum(x for x, _, _ in dc) / len(dc))
    avg_y = int(sum(y for _, y, _ in dc) / len(dc))
    cv2.putText(output, str(len(cluster_beads[i])), (avg_x - 15, avg_y + 15), fontFace=0, fontScale=2.0, color=color,
                thickness=4)

# Combine original image analyzed output on one side
image_and_output = np.hstack([image, output])

# Show the original and output image side by side
cv2.imshow("output", image_and_output)
cv2.waitKey(0)

# Save the original and output image
cv2.imwrite('images/output.png', image_and_output)