import random

def pick_random_coordinate(coordinates):
    return random.choice(coordinates)

# Example usage
if __name__ == "__main__":
    coordinates = [(-8.5, -1.5), (-6.0, -1.5), (-3.6, -1.5), (-3.3, -3.2), (-6.0, -3.2), (-8.5, -3.2), 
                    (-3.3, -5.2), (-6.0, -5.2), (-8.5, -5.2), (-3.3, -7.0), (-6.0, -7.0), (-8.5, -7.0),
                    (-3.3, -8.7), (-6.0, -8.7), (-8.5, -8.7), (-3.3, -10.6), (-6.0, -10.6), 
                    (-8.5, -10.6), (-3.3, -12.5), (-6.0, -12.5), (-8.5, -12.5) ]  # List of (x, y) coordinates

    random_coordinate = pick_random_coordinate(coordinates)
    print(random_coordinate)
