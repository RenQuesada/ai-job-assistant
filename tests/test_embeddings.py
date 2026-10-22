from core.embeddings import dot_product, group_skills

# --- dot_product ---

def test_dot_product_same_direction():
    assert dot_product([1, 0], [1, 0]) == 1

def test_dot_product_perpendicular():
    assert dot_product([1, 0], [0, 1]) == 0

def test_dot_product_multiplies_and_sums_all_elements():
    # 1*4 + 2*5 + 3*6
    assert dot_product([1, 2, 3], [4, 5, 6]) == 32

def test_dot_product_opposite():
    assert dot_product([1, 0], [-1, 0]) == -1

# --- group_skills ---

TEST_THRESHOLD = 0.5

def test_group_skills_merges_identical_vectors():
    skill_map = group_skills(["React", "React.js"], [[1, 0], [1, 0]])
    assert skill_map == {"React": "React", "React.js": "React"}

def test_group_skills_keeps_unrelated_skills_separate():
    skill_map = group_skills(["Java", "Python"], [[1, 0], [0, 1]])
    assert skill_map == {"Java": "Java", "Python": "Python"}

def test_group_skills_merges_at_exact_threshold():
    skill_map = group_skills(["React", "React.js"], [[1, 0], [0.5, 0.5]], threshold=TEST_THRESHOLD)
    assert skill_map == {"React": "React", "React.js": "React"}

def test_group_skills_keeps_separate_just_below_threshold():
    skill_map = group_skills(["REST APIs", "RESTful services"], [[1, 0], [0.49, 0.49]], threshold=TEST_THRESHOLD)
    assert skill_map == {"REST APIs": "REST APIs", "RESTful services": "RESTful services"}

def test_group_skills_uses_first_skill_as_canonical():
    skill_map = group_skills(["React.js", "React"], [[1, 0], [1, 0]])
    assert skill_map == {"React.js": "React.js", "React": "React.js"}

def test_group_skills_merges_verified_pair_below_threshold():
    # [1, 0] and [0, 1] score 0, but the pair is verified
    skill_map = group_skills(
        ["REST APIs", "RESTful services"],
        [[1, 0], [0, 1]],
        verified_pairs={frozenset(("REST APIs", "RESTful services"))},
    )
    assert skill_map == {"REST APIs": "REST APIs", "RESTful services": "REST APIs"}