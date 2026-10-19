from core.embeddings import dot_product

def test_dot_product_same_direction():
    assert dot_product([1, 0], [1, 0]) == 1

def test_dot_product_perpendicular():
    assert dot_product([1, 0], [0, 1]) == 0

def test_dot_product_multiplies_and_sums_all_elements():
    # 1*4 + 2*5 + 3*6
    assert dot_product([1, 2, 3], [4, 5, 6]) == 32

def test_dot_product_opposite():
    assert dot_product([1, 0], [-1, 0]) == -1