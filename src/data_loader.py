import json


def load_batch(K=50, data_path='maps.json'):
    data = json.load(open(data_path))
    if K > len(data):
        raise IndexError("K should be no greater than size of dataset. size=" + str(len(data)))
    objects = list(map(lambda x: x[0], data[:K]))
    feats = list(map(lambda x: x[1], data[:K]))
    return objects, feats
