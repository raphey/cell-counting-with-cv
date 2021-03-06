__author__ = 'raphey'

import numpy as np
import cv2
import matplotlib.pyplot as plt


# Tool to retrieve clicks
class ClickClass():
    def __init__(self, filepath):
        self.fname = filepath
        self.img = cv2.imread(self.fname)
        self.point = ()

    def getCoord(self):
        fig = plt.figure()
        fig.add_subplot(111)
        plt.imshow(self.img)
        fig.canvas.mpl_connect('button_press_event', self.__onclick__)
        plt.show()
        return self.point

    def __onclick__(self, click):
        self.point = (click.xdata, click.ydata)
        print(np.round(self.point))
        return self.point


def print_positive_examples():
    click = ClickClass('images/test_array_1.png')
    click.getCoord()


def show_positive_coords(img, pos_coords):
    output = img.copy()
    for x, y in pos_coords:
        cv2.circle(output, (x, y), 3, (0, 0, 255), 1)

    cv2.imshow("output", output)
    cv2.waitKey(0)


def save_training_data_from_coords(img, save_directory, pos_coords, pos_radius=0, neg_radius=3,
                                   neg_stride=2, edge_border=12):
    """
    Saves a series of 9x9 sections of img based on positive example coordinate pairs.
    Also grabs positive images located within pos_radius of given coordinate pairs.
    Negative examples are generated by moving with neg_stride across image, within
    edge_border from edge, grabbing images that are at least neg_radius from
    positive coordinates.
    """

    # Get all integer coords within pos_radius of origin
    pos_shift_pairs = [(x, y) for x in range(-pos_radius, pos_radius + 1)
                       for y in range(-pos_radius, pos_radius + 1)
                       if x ** 2 + y ** 2 <= pos_radius ** 2]

    # Get all integer coords *less than* neg radius of origin
    neg_shift_pairs = [(x, y) for x in range(-neg_radius, neg_radius + 1)
                       for y in range(-neg_radius, neg_radius + 1)
                       if x ** 2 + y ** 2 < neg_radius ** 2]

    # Set of coordinates prohibited for negative examples (too close to positive examples)
    non_negative_coords = set()

    bead_counter = 0

    for x, y in pos_coords:
        for x_adj, y_adj in pos_shift_pairs:
            if not (4 <= x + x_adj < len(img[0]) - 4 and 4 <= y + y_adj < len(img) - 4):
                continue
            bead_img = grab_9x9_image_section(img, x + x_adj, y + y_adj)
            count_label = str(1000000 + bead_counter)[1:]
            cv2.imwrite('{}/beads/sample_{}_x{}_y{}.png'.format(
                        save_directory, count_label, x + x_adj, y + y_adj), bead_img)
            bead_counter += 1
        for x_adj, y_adj in neg_shift_pairs:
            non_negative_coords.add((x + x_adj, y + y_adj))

    non_bead_counter = 0

    for x in range(edge_border, len(img[0]) - edge_border, neg_stride):
        for y in range(edge_border, len(img) - edge_border, neg_stride):
            if (x, y) in non_negative_coords:
                continue
            non_bead_img = grab_9x9_image_section(img, x, y)
            count_label = str(1000000 + non_bead_counter)[1:]
            cv2.imwrite('{}/non_beads/sample_{}_x{}_y{}.png'.format(
                        save_directory, count_label, x, y), non_bead_img)
            non_bead_counter += 1


def grab_9x9_image_section(img, x, y):
    return img[y - 4: y + 5, x - 4: x + 5]


if __name__ == '__main__':
    # Load image and convert image to grayscale
    image_path = 'images/test_array_1.png'
    image = cv2.imread(image_path)
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Load positive example coordinates from csv
    pos_data = np.loadtxt(open("training_data/set3/bead_coords_refined.csv", "rb"), delimiter=",", skiprows=1, dtype=int)

    save_training_data_from_coords(grayscale_image, 'training_data/set3', pos_data, pos_radius=1, neg_radius=3)