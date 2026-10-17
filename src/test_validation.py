from data_validation import is_valid
import pytest
#test
def test_valid_post():
    post = {
        "id" : 101,
        "userId" : 5,
        "title" : "Hello",
        "body" : "Example"
    }
    valid,reason = is_valid(post)
    assert valid is True
    assert reason is None

@pytest.mark.parametrize("invalid_title",[None,"","  ",123,True])

def test_invalid_titles(invalid_title):
    post = {
        "id":101,
        "userId":5,
        "title":invalid_title,
        "body":"Example"
    }
    valid,reason = is_valid(post)
    assert valid is False
    assert reason == "Invalid title"

@pytest.mark.parametrize("invalid_id",[0,-5,True,"101",None])

def test_invalid_ids(invalid_id):
    post = {
        "id":invalid_id,
        "userId":5,
        "title":"Test",
        "body":"Example"
    }
    valid,reason = is_valid(post)
    assert valid is False
    assert reason == "Invalid ID"

@pytest.mark.parametrize("invalid_userid",[0,-10,True,"5",None])
def test_invalid_userids(invalid_userid):
    post = {
        "id":5,
        "userId":invalid_userid,
        "title":"Test",
        "body":"Example"
    }
    valid,reason = is_valid(post)
    assert valid is False
    assert reason == "Invalid userId"

@pytest.mark.parametrize("invalid_body",[None, "", "   ", 123, False])
def test_invalid_bodies(invalid_body):
    post = {
        "id":5,
        "userId":100,
        "title":"Test",
        "body":invalid_body
    }
    valid,reason = is_valid(post)
    assert valid is False
    assert reason == "Invalid body"

@pytest.mark.parametrize("field",["id","userId","title","body"])
def test_missing_fields(field):
    post = {
            "id":5,
            "userId":100,
            "title":"Test",
            "body":"Hello"
        }
    post_copy = post.copy()
    post_copy.pop(field)
    valid,reason = is_valid(post_copy)
    assert valid is False
    assert reason is not None