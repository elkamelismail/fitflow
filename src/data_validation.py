def is_valid(post):
    if type(post.get("id")) != int or post["id"]<=0:
        return (False,"Invalid ID")
    if isinstance(post.get("title"),str) == False or post["title"].strip() == "":
        return (False,"Invalid title")
    if type(post.get("userId")) != int or post["userId"]<=0:
        return (False,"Invalid userId")
    if isinstance(post.get("body"),str) == False or post["body"].strip() == "":
        return (False,"Invalid body")
    return (True,None)
                        